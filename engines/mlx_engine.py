"""MLX engine — small local LLM on Apple Silicon via mlx-lm.

Loads a small Gemma 4 instruction model the first time it is used. Override
with env var:  AUTO_TRANSLATE_MLX_MODEL

  default : Rapid42/gemma-4-E2B-it-MLX   (E2B ~2.3B eff. params, fast/light)
  larger  : Rapid42/gemma-4-E4B-it-MLX   (E4B ~4.5B eff. params, better quality)
  smaller : unsloth/gemma-4-E2B-it-UD-MLX-4bit  (4-bit, lowest memory)
"""

import os
import threading

from languages import NAMES

NAME = "mlx"
LABEL = "MLX — Gemma 4 E2B (Apple Silicon)"

MODEL = os.environ.get(
    "AUTO_TRANSLATE_MLX_MODEL", "Rapid42/gemma-4-E2B-it-MLX"
)

_lock = threading.Lock()
_loaded = None  # (model, tokenizer)


def is_available():
    try:
        import mlx_lm  # noqa: F401
        return True
    except Exception:
        return False


def _ensure_loaded(on_status):
    global _loaded
    if _loaded is None:
        from mlx_lm import load
        if on_status:
            on_status(f"LLM を読み込み中 ({MODEL})…")
        _loaded = load(MODEL)
    return _loaded


def _lang(code):
    return NAMES.get(code, code)


def translate(text, src, tgt, on_status=None):
    if not text.strip():
        return ""
    from mlx_lm import generate

    with _lock:
        model, tokenizer = _ensure_loaded(on_status)
        src_name = "the source language" if src == "auto" else _lang(src)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional translation engine. Translate the "
                    "user's text accurately and naturally. Output ONLY the "
                    "translation, with no explanations, quotes, or notes."
                ),
            },
            {
                "role": "user",
                "content": f"Translate from {src_name} to {_lang(tgt)}:\n\n{text}",
            },
        ]
        # Gemma 4 ships a multimodal processor whose chat template can return a
        # dict; return_dict=False forces a flat token list that generate() takes.
        prompt = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_dict=False
        )
        out = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=max(64, len(text) * 3),
            verbose=False,
        )
        return out.strip()
