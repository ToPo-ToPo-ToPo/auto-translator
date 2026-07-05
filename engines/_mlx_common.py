"""Shared implementation for the MLX engines (Gemma 4 E2B / E4B).

Each MLX engine module creates one MlxModel and re-exports its methods. The
model is resolved as: AUTO_TRANSLATE_MLX_*_MODEL env override → a locally-built
copy under ~/.cache/auto-translator/mlx → otherwise the published HF repo (auto-
downloaded on first use). Convert and load must use the same mlx-vlm version,
hence the pin in pyproject.
"""

import os
import platform
import sys
import threading
import time

from engines import _idle
from languages import NAMES

CACHE_DIR = os.path.expanduser("~/.cache/auto-translator/mlx")


def is_applicable():
    """MLX (mlx-vlm) only runs on Apple Silicon. On any other OS/arch the MLX
    engines are hidden entirely (the dependency isn't installed there either)."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def _download_with_progress(repo, on_status):
    """Download `repo` into the HF cache, reporting % / GB progress via on_status
    (which the app routes to the log panel). Returns the local snapshot path."""
    from huggingface_hub import snapshot_download
    import time as _time

    state = {"t": 0.0}

    base = None
    try:
        from tqdm.auto import tqdm as base
    except Exception:
        base = None

    if base is None:                      # no tqdm available — plain download
        if on_status:
            on_status(f"MLXモデルをダウンロード中: {repo}")
        return snapshot_download(repo)

    class _LogTqdm(base):
        def update(self, n=1):
            r = super().update(n)
            try:
                total = self.total or 0
                if total > 5_000_000 and on_status:   # only big files (weights)
                    now = _time.time()
                    done = self.n >= total
                    if now - state["t"] > 1.0 or done:
                        state["t"] = now
                        on_status(
                            f"ダウンロード中 {self.n / total * 100:4.1f}%  "
                            f"{self.n / 1e9:.2f} / {total / 1e9:.2f} GB"
                        )
            except Exception:
                pass
            return r

    if on_status:
        on_status(f"MLXモデルをダウンロード開始: {repo}")
    path = snapshot_download(repo, tqdm_class=_LogTqdm)
    if on_status:
        on_status("ダウンロード完了。読み込み中…")
    return path


def _cached_snapshot(repo):
    """Return the local snapshot path only if `repo` is fully in the HF cache
    *with its weights present* (no network), else None. A partial cache (e.g. an
    interrupted download that fetched config but not the .safetensors) returns
    None so the caller falls back to completing the download."""
    import glob
    try:
        from huggingface_hub import snapshot_download
        path = snapshot_download(repo, local_files_only=True)
    except Exception:
        return None
    has_weights = glob.glob(os.path.join(path, "*.safetensors")) or glob.glob(
        os.path.join(path, "**", "*.safetensors"), recursive=True
    )
    return path if has_weights else None


class MlxModel:
    def __init__(self, name, label, subdir, hf_repo, env_var, size_gb=0):
        self.NAME = name
        self.LABEL = label
        self.local_path = os.path.join(CACHE_DIR, subdir)   # locally-built copy
        self.hf_repo = hf_repo                              # published fallback
        self.env_var = env_var
        self.size_gb = size_gb              # approx download size (for the prompt)
        self._lock = threading.Lock()
        self._loaded = None                 # (model, processor)
        self._config = None
        self._last_used = 0.0               # time.monotonic() of last use
        self._watcher_started = False

    def pending_download(self):
        """If running this engine now would trigger a model download, return
        {'size_gb': N}. Return None if the model is already local/cached (loaded
        offline, no download)."""
        if self._loaded is not None:
            return None
        m = self.resolve(prefer_cache=True)
        if os.path.isdir(os.path.expanduser(m)):
            return None
        return {"size_gb": self.size_gb}

    def resolve(self, prefer_cache=False):
        """env override → local build → (cached HF snapshot) → published HF repo.

        With prefer_cache=True, if the HF repo is already fully cached, return its
        local snapshot path so loading is fully offline (no network/etag checks,
        no accidental re-download)."""
        env = os.environ.get(self.env_var)
        if env:
            return env
        if os.path.isdir(self.local_path):
            return self.local_path
        if prefer_cache:
            cached = _cached_snapshot(self.hf_repo)
            if cached:
                return cached
        return self.hf_repo                 # mlx-vlm downloads this on first use

    def _model_ready(self):
        m = self.resolve()
        if os.path.isdir(os.path.expanduser(m)):
            return True
        # An HF repo id (org/name, not a filesystem path) is downloadable.
        return "/" in m and not m.startswith(("/", "~", "."))

    def is_available(self):
        # Cheap presence check — avoid importing mlx_vlm at startup (slow).
        import importlib.util
        if importlib.util.find_spec("mlx_vlm") is None:
            return False
        return self._model_ready()

    def unavailable_reason(self):
        if not is_applicable():
            return "MLX は Apple Silicon (macOS) 専用です。このOSでは利用できません。"
        import importlib.util
        if importlib.util.find_spec("mlx_vlm") is None:
            return (
                "MLX（mlx-vlm）が読み込めません。Apple Silicon の Mac で `uv sync` を"
                "実行すると導入されます。"
            )
        if not self._model_ready():
            return f"MLXモデルを解決できません: {self.resolve()}"
        return None

    def _ensure(self, on_status):
        if self._loaded is None:
            from mlx_vlm import load
            from mlx_vlm.utils import load_config
            m = self.resolve(prefer_cache=True)   # use cached snapshot if present
            if os.path.isdir(os.path.expanduser(m)):
                if on_status:
                    on_status(f"MLXモデルを準備中 ({m})…（キャッシュから）")
            else:
                # Not local/cached — download ourselves so progress is logged.
                m = _download_with_progress(m, on_status)
            self._loaded = load(m)
            self._config = load_config(m)
            self._start_watcher()
        self._last_used = time.monotonic()
        return self._loaded, self._config

    def _start_watcher(self):
        """Begin idle-unload polling for this model (once). Called while the
        lock is held, right after the first successful load."""
        if self._watcher_started:
            return
        self._watcher_started = True
        _idle.start_watcher(
            self.NAME,
            is_loaded=lambda: self._loaded is not None,
            seconds_idle=lambda: time.monotonic() - self._last_used,
            unload=self.unload,
        )

    def unload(self):
        """Drop the resident model so its memory is freed. Idempotent and safe
        to call from the idle watcher; re-checks idleness under the lock so a
        translation that just started isn't unloaded out from under itself."""
        timeout = _idle.timeout_sec()
        with self._lock:
            if self._loaded is None:
                return
            if timeout > 0 and time.monotonic() - self._last_used < timeout:
                return  # got used again while we were waiting for the lock
            self._loaded = None
            self._config = None
        _idle.free_accelerator_memory()
        print(f"[{self.NAME}] 一定時間未使用のため MLX モデルをメモリから解放しました。")

    def translate(self, text, src, tgt, on_status=None):
        if not text.strip():
            return ""
        import settings
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template

        with self._lock:
            (model, processor), config = self._ensure(on_status)
            src_name = "the source language" if src == "auto" else NAMES.get(src, src)
            msg = (
                f"Translate from {src_name} to {NAMES.get(tgt, tgt)}. "
                f"Output only the translation, with no explanations.\n\n{text}"
            )
            prompt = apply_chat_template(processor, config, msg, num_images=0)
            res = generate(
                model, processor, prompt,
                max_tokens=settings.max_tokens(max(64, len(text) * 3)),
                temperature=settings.temperature(), verbose=False,
            )
            self._last_used = time.monotonic()
            return (res if isinstance(res, str) else getattr(res, "text", str(res))).strip()

    def alternatives(self, sentence, selection, src, tgt, on_status=None):
        """Return alternative wordings for `selection` within `sentence` (used
        by the post-edit UI). Empty list if there's nothing to work with."""
        if not (sentence.strip() and selection.strip()):
            return []
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template

        from engines._llm_util import alt_prompt, parse_alternatives

        with self._lock:
            (model, processor), config = self._ensure(on_status)
            msg = alt_prompt(sentence, selection, src, tgt)
            prompt = apply_chat_template(processor, config, msg, num_images=0)
            # A little warmth here gives more varied wording suggestions.
            res = generate(model, processor, prompt, max_tokens=160,
                           temperature=0.6, verbose=False)
            self._last_used = time.monotonic()
        raw = res if isinstance(res, str) else getattr(res, "text", str(res))
        return parse_alternatives(raw, selection, sentence=sentence)

    def rephrase(self, source_text, sentence, selection, replacement,
                 src, tgt, on_status=None):
        """Rewrite the whole translation so it uses `replacement` (the wording
        the user picked) naturally — the DeepL-style re-flow after choosing an
        alternative. Returns the revised translation."""
        if not (sentence.strip() and replacement.strip()):
            return sentence
        from mlx_vlm import generate
        from mlx_vlm.prompt_utils import apply_chat_template

        from engines._llm_util import parse_rephrase, rephrase_prompt

        with self._lock:
            (model, processor), config = self._ensure(on_status)
            msg = rephrase_prompt(source_text, sentence, selection,
                                  replacement, src, tgt)
            prompt = apply_chat_template(processor, config, msg, num_images=0)
            res = generate(model, processor, prompt,
                           max_tokens=max(128, len(sentence) * 3),
                           temperature=0.2, verbose=False)
            self._last_used = time.monotonic()
        raw = res if isinstance(res, str) else getattr(res, "text", str(res))
        return parse_rephrase(raw, sentence)
