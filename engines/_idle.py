"""Idle model unloading — shared by the LLM engines (MLX, llama.cpp).

An LLM keeps a few GB resident once loaded. If the app is left running but not
used for a while, we release the model from memory; the next translation simply
reloads it. One lightweight daemon thread per engine polls an "is it idle?"
predicate and calls the engine's own (thread-safe) unload function.

Idle timeout is `AUTO_TRANSLATE_IDLE_UNLOAD_SEC` seconds (default 300 = 5 min).
Set it to 0 (or a negative value) to disable automatic unloading entirely.
"""

import os
import threading
import time


def timeout_sec(default=300.0):
    """Idle timeout in seconds from the env (default 5 min); <=0 disables it."""
    raw = os.environ.get("AUTO_TRANSLATE_IDLE_UNLOAD_SEC")
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def free_accelerator_memory():
    """Best-effort release of cached GPU/Metal buffers after dropping a model.

    Runs a GC pass (so the model object is actually collected) and clears MLX's
    Metal buffer cache if MLX is present. All of it is optional/guarded — this
    must never raise into the polling thread."""
    import gc

    gc.collect()
    try:
        import mlx.core as mx

        if hasattr(mx, "clear_cache"):
            mx.clear_cache()
        elif hasattr(mx, "metal") and hasattr(mx.metal, "clear_cache"):
            mx.metal.clear_cache()
    except Exception:
        pass


def start_watcher(name, is_loaded, seconds_idle, unload):
    """Spawn one daemon thread that unloads an idle model.

    name          label for logging / the thread name
    is_loaded()   -> bool  : whether the model is currently resident
    seconds_idle() -> float : seconds since the model was last used
    unload()               : drop the model (must be idempotent + thread-safe,
                             and re-check idleness itself to avoid a race with a
                             translation that started while we were waiting).

    No-op (returns without starting a thread) when the timeout is disabled.
    """
    timeout = timeout_sec()
    if timeout <= 0:
        return
    poll = max(5.0, min(30.0, timeout / 2))

    def loop():
        while True:
            time.sleep(poll)
            try:
                if is_loaded() and seconds_idle() >= timeout:
                    unload()
            except Exception:
                pass

    threading.Thread(target=loop, name=f"idle-unload:{name}", daemon=True).start()
