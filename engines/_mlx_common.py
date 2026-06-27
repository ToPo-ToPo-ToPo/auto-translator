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

from languages import NAMES

CACHE_DIR = os.path.expanduser("~/.cache/auto-translator/mlx")


def is_applicable():
    """MLX (mlx-vlm) only runs on Apple Silicon. On any other OS/arch the MLX
    engines are hidden entirely (the dependency isn't installed there either)."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


class MlxModel:
    def __init__(self, name, label, subdir, hf_repo, env_var):
        self.NAME = name
        self.LABEL = label
        self.local_path = os.path.join(CACHE_DIR, subdir)   # locally-built copy
        self.hf_repo = hf_repo                              # published fallback
        self.env_var = env_var
        self._lock = threading.Lock()
        self._loaded = None                 # (model, processor)
        self._config = None

    def resolve(self):
        """env override → local build (if present) → published HF repo."""
        env = os.environ.get(self.env_var)
        if env:
            return env
        if os.path.isdir(self.local_path):
            return self.local_path
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
            m = self.resolve()
            if on_status:
                hint = "（初回はHFからDLします）" if not os.path.isdir(m) else ""
                on_status(f"MLXモデルを準備中 ({m})…{hint}")
            self._loaded = load(m)
            self._config = load_config(m)
        return self._loaded, self._config

    def translate(self, text, src, tgt, on_status=None):
        if not text.strip():
            return ""
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
                max_tokens=max(64, len(text) * 3), verbose=False,
            )
            return (res if isinstance(res, str) else getattr(res, "text", str(res))).strip()
