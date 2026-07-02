"""Idle model unloading — shared by the LLM engines (MLX, llama.cpp).

An LLM keeps a few GB resident once loaded. If the app is left running but not
used for a while, we release the model from memory; the next translation simply
reloads it. One lightweight daemon thread per engine polls an "is it idle?"
predicate and calls the engine's own (thread-safe) unload function.

Idle timeout comes from the settings panel (`idle_unload_sec`), overridable by
`AUTO_TRANSLATE_IDLE_UNLOAD_SEC`. Either at 0 (or negative) disables unloading.
The watcher re-reads the timeout every poll, so changing it in the UI takes
effect without a restart.
"""

import os
import threading
import time

import settings


def timeout_sec(default=300.0):
    """Current idle timeout in seconds; <=0 disables unloading.

    The env var, when set, wins (explicit operator override); otherwise the
    value comes from the live settings so the UI can change it at runtime."""
    raw = os.environ.get("AUTO_TRANSLATE_IDLE_UNLOAD_SEC")
    if raw not in (None, ""):
        try:
            return float(raw)
        except ValueError:
            pass
    try:
        return float(settings.idle_unload_sec())
    except Exception:
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

    The thread stays alive even while unloading is disabled (timeout <= 0), so
    re-enabling it from the settings panel resumes without a restart.
    """

    def loop():
        while True:
            timeout = timeout_sec()
            time.sleep(max(5.0, min(30.0, (timeout / 2) if timeout > 0 else 15.0)))
            try:
                timeout = timeout_sec()
                if timeout > 0 and is_loaded() and seconds_idle() >= timeout:
                    unload()
            except Exception:
                pass

    threading.Thread(target=loop, name=f"idle-unload:{name}", daemon=True).start()
