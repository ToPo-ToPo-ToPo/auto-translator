"""MLX engine — small local LLM on Apple Silicon via mlx-vlm.

Uses a self-converted Gemma 4 E2B (MLX 4-bit) stored locally — it is NOT
published to a model hub. IMPORTANT: the checkpoint must be converted and
loaded with the *same* mlx-vlm version, so this app pins mlx-vlm==0.6.3.

Build the model once with:  uv run python tools/build_mlx_model.py
Override the location/model via env:

  AUTO_TRANSLATE_MLX_MODEL   local path (default below) or an HF repo id
"""

import os
import threading

from languages import NAMES

NAME = "mlx"
LABEL = "Gemma 4 E2B (MLX)"

DEFAULT_MODEL = os.path.expanduser(
    "~/.cache/auto-translator/mlx/gemma-4-E2B-it-qat-mlx-4bit"
)
MODEL = os.environ.get("AUTO_TRANSLATE_MLX_MODEL", DEFAULT_MODEL)

_lock = threading.Lock()
_loaded = None   # (model, processor)
_config = None


def _model_ready():
    """The default model is local — present if its folder exists. An HF repo id
    override (org/name, not a filesystem path) is assumed downloadable."""
    if os.path.isdir(os.path.expanduser(MODEL)):
        return True
    return "/" in MODEL and not MODEL.startswith(("/", "~", "."))


def is_available():
    try:
        import mlx_vlm  # noqa: F401
    except Exception:
        return False
    return _model_ready()


def unavailable_reason():
    try:
        import mlx_vlm  # noqa: F401
    except Exception as e:
        return (
            "MLX（mlx-vlm）が読み込めません。Apple Silicon の Mac で `uv sync` を"
            f"実行すると導入されます。（詳細: {type(e).__name__}: {e}）"
        )
    if not _model_ready():
        return (
            "MLXモデルがまだ作成されていません。プロジェクトフォルダで "
            "`uv run python tools/build_mlx_model.py` を実行すると、公式重みから"
            f"変換して用意します（約9.5GBのDL→約3.3GB）。場所: {MODEL}"
        )
    return None


def _ensure(on_status):
    global _loaded, _config
    if _loaded is None:
        from mlx_vlm import load
        from mlx_vlm.utils import load_config
        if on_status:
            on_status(f"MLXモデルを読み込み中 ({os.path.basename(MODEL)})…")
        _loaded = load(MODEL)
        _config = load_config(MODEL)
    return _loaded, _config


def _lang(code):
    return NAMES.get(code, code)


def translate(text, src, tgt, on_status=None):
    if not text.strip():
        return ""
    from mlx_vlm import generate
    from mlx_vlm.prompt_utils import apply_chat_template

    with _lock:
        (model, processor), config = _ensure(on_status)
        src_name = "the source language" if src == "auto" else _lang(src)
        msg = (
            f"Translate from {src_name} to {_lang(tgt)}. "
            f"Output only the translation, with no explanations.\n\n{text}"
        )
        prompt = apply_chat_template(processor, config, msg, num_images=0)
        res = generate(
            model, processor, prompt,
            max_tokens=max(64, len(text) * 3), verbose=False,
        )
        out = res if isinstance(res, str) else getattr(res, "text", str(res))
        return out.strip()
