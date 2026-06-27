"""Shared implementation for the MLX engines (Gemma 4 E2B / E4B).

Each MLX engine module creates one MlxModel and re-exports its methods. Models
are self-converted with mlx-vlm 0.6.3 and kept local (not published); convert
and load must use the same mlx-vlm version, hence the pin in pyproject.
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
    def __init__(self, name, label, subdir, env_var, build_arg):
        self.NAME = name
        self.LABEL = label
        self.DEFAULT_MODEL = os.path.join(CACHE_DIR, subdir)
        self.MODEL = os.environ.get(env_var, self.DEFAULT_MODEL)
        self.build_arg = build_arg          # e.g. "e2b" — shown in the build hint
        self._lock = threading.Lock()
        self._loaded = None                 # (model, processor)
        self._config = None

    def _model_ready(self):
        if os.path.isdir(os.path.expanduser(self.MODEL)):
            return True
        # An HF repo id (org/name, not a filesystem path) is assumed downloadable.
        return "/" in self.MODEL and not self.MODEL.startswith(("/", "~", "."))

    def is_available(self):
        # Cheap presence check — avoid importing mlx_vlm at startup (slow).
        import importlib.util
        if importlib.util.find_spec("mlx_vlm") is None:
            return False
        return self._model_ready()

    def unavailable_reason(self):
        if not is_applicable():
            return "MLX は Apple Silicon (macOS) 専用です。このOSでは利用できません。"
        try:
            import mlx_vlm  # noqa: F401
        except Exception as e:
            return (
                "MLX（mlx-vlm）が読み込めません。Apple Silicon の Mac で `uv sync` を"
                f"実行すると導入されます。（詳細: {type(e).__name__}: {e}）"
            )
        if not self._model_ready():
            return (
                "MLXモデルがまだ作成されていません。プロジェクトフォルダで "
                f"`uv run python tools/build_mlx_model.py {self.build_arg}` を実行すると、"
                f"公式重みから変換して用意します。場所: {self.MODEL}"
            )
        return None

    def _ensure(self, on_status):
        if self._loaded is None:
            from mlx_vlm import load
            from mlx_vlm.utils import load_config
            if on_status:
                on_status(f"MLXモデルを読み込み中 ({os.path.basename(self.MODEL)})…")
            self._loaded = load(self.MODEL)
            self._config = load_config(self.MODEL)
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
