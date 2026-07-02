"""llama.cpp engine — small local LLM via llama-cpp-python + a GGUF model.

Chosen for portability: a single GGUF runs on Apple Silicon (Metal), Intel,
Linux and Windows. Default model is Gemma 4 E2B (Q4_0), auto-downloaded from
Hugging Face on first use (like Argos models). Override via env vars:

  AUTO_TRANSLATE_GGUF        local .gguf path (highest priority, no download)
  AUTO_TRANSLATE_GGUF_REPO   HF repo id    (default: google/gemma-4-E2B-it-qat-q4_0-gguf)
  AUTO_TRANSLATE_GGUF_FILE   file in repo  (default: gemma-4-E2B_q4_0-it.gguf)

Step up to E4B (better quality, more RAM) by pointing the repo/file env vars at
google/gemma-4-E4B-it-qat-q4_0-gguf / gemma-4-E4B_q4_0-it.gguf.
"""

import os
import threading
import time

from engines import _idle
from languages import NAMES

NAME = "llamacpp"
LABEL = "Gemma 4 E2B (llama.cpp)"

GGUF_PATH = os.environ.get("AUTO_TRANSLATE_GGUF", "")
GGUF_REPO = os.environ.get(
    "AUTO_TRANSLATE_GGUF_REPO", "google/gemma-4-E2B-it-qat-q4_0-gguf"
)
GGUF_FILE = os.environ.get("AUTO_TRANSLATE_GGUF_FILE", "gemma-4-E2B_q4_0-it.gguf")

_lock = threading.Lock()
_llm = None
_resolved_path = None
_last_used = 0.0
_idle_timeout = _idle.timeout_sec()
_watcher_started = False


def is_applicable():
    # Optional engine: only show it in the UI when actually installed
    # (uv sync --extra llamacpp). Otherwise it's hidden, not shown as broken.
    import importlib.util
    return importlib.util.find_spec("llama_cpp") is not None


def is_available():
    # Cheap presence check — avoid importing llama_cpp at startup (slow).
    import importlib.util
    return importlib.util.find_spec("llama_cpp") is not None


def unavailable_reason():
    """Human-readable reason this engine can't be used (or None if it can)."""
    try:
        import llama_cpp  # noqa: F401
        return None
    except Exception as e:
        return (
            "llama.cpp（llama-cpp-python）は既定では導入されません（任意エンジン）。"
            "使う場合はプロジェクトフォルダで `uv sync --extra llamacpp` を実行してください。"
            "macOS では MLX エンジンの利用を推奨します。"
            f"（詳細: {type(e).__name__}: {e}）"
        )


def _model_path(on_status):
    """Return a local GGUF path, downloading the default model if needed."""
    global _resolved_path
    if _resolved_path:
        return _resolved_path
    if GGUF_PATH:
        if not os.path.isfile(GGUF_PATH):
            raise RuntimeError(f"GGUF が見つかりません: {GGUF_PATH}")
        _resolved_path = GGUF_PATH
        return _resolved_path
    from huggingface_hub import hf_hub_download
    if on_status:
        on_status(f"モデルを準備中 ({GGUF_REPO})… 初回は数GBのDLが入ります")
    _resolved_path = hf_hub_download(repo_id=GGUF_REPO, filename=GGUF_FILE)
    return _resolved_path


def _ensure_loaded(on_status):
    global _llm, _last_used, _watcher_started
    if _llm is None:
        from llama_cpp import Llama
        path = _model_path(on_status)
        if on_status:
            on_status("LLM を読み込み中…")
        _llm = Llama(
            model_path=path,
            n_ctx=4096,
            n_gpu_layers=-1,   # offload to Metal/GPU where available; CPU otherwise
            verbose=False,
        )
        if not _watcher_started:
            _watcher_started = True
            _idle.start_watcher(
                NAME,
                is_loaded=lambda: _llm is not None,
                seconds_idle=lambda: time.monotonic() - _last_used,
                unload=unload,
            )
    _last_used = time.monotonic()
    return _llm


def unload():
    """Drop the resident LLM so its memory is freed. Idempotent and safe to call
    from the idle watcher (re-checks idleness under the lock)."""
    global _llm
    with _lock:
        if _llm is None:
            return
        if time.monotonic() - _last_used < _idle_timeout:
            return
        _llm = None
    _idle.free_accelerator_memory()
    print(f"[{NAME}] 一定時間未使用のため LLM をメモリから解放しました。")


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
        global _last_used
        _last_used = time.monotonic()
        return resp["choices"][0]["message"]["content"].strip()


def alternatives(sentence, selection, src, tgt, on_status=None):
    """Return alternative wordings for `selection` within `sentence` (used by
    the post-edit UI). Empty list if there's nothing to work with."""
    if not (sentence.strip() and selection.strip()):
        return []
    from engines._llm_util import alt_prompt, parse_alternatives

    with _lock:
        llm = _ensure_loaded(on_status)
        resp = llm.create_chat_completion(
            messages=[{"role": "user", "content": alt_prompt(sentence, selection, src, tgt)}],
            max_tokens=160,
            temperature=0.4,
        )
        global _last_used
        _last_used = time.monotonic()
    return parse_alternatives(resp["choices"][0]["message"]["content"], selection)
