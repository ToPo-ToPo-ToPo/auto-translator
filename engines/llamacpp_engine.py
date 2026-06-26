"""llama.cpp engine — small local LLM via llama-cpp-python + a GGUF file.

Point this at a small Gemma 4 GGUF (e.g. gemma-4-E2B-it / gemma-4-E4B-it).
Set the model path with env var:  AUTO_TRANSLATE_GGUF
Engine reports unavailable until both the package and a readable GGUF exist.
"""

import os
import threading

from languages import NAMES

NAME = "llamacpp"
LABEL = "llama.cpp — Gemma 4 GGUF"

MODEL_PATH = os.environ.get("AUTO_TRANSLATE_GGUF", "")

_lock = threading.Lock()
_llm = None


def is_available():
    if not MODEL_PATH or not os.path.isfile(MODEL_PATH):
        return False
    try:
        import llama_cpp  # noqa: F401
        return True
    except Exception:
        return False


def _ensure_loaded(on_status):
    global _llm
    if _llm is None:
        from llama_cpp import Llama
        if on_status:
            on_status(f"GGUF を読み込み中 ({os.path.basename(MODEL_PATH)})…")
        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,
            n_threads=os.cpu_count(),
            verbose=False,
        )
    return _llm


def _lang(code):
    return NAMES.get(code, code)


def translate(text, src, tgt, on_status=None):
    if not text.strip():
        return ""
    with _lock:
        llm = _ensure_loaded(on_status)
        src_name = "the source language" if src == "auto" else _lang(src)
        resp = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional translation engine. Output ONLY "
                        "the translation, with no explanations or quotes."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Translate from {src_name} to {_lang(tgt)}:\n\n{text}",
                },
            ],
            max_tokens=max(64, len(text) * 3),
            temperature=0.2,
        )
        return resp["choices"][0]["message"]["content"].strip()
