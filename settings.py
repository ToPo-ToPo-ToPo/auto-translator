"""User-adjustable settings, persisted as JSON and shared by the UI + engines.

The settings panel (⚙ in the UI) reads and writes these via /api/settings. They
are stored in ~/.config/auto-translator/settings.json so they survive restarts.
Engines read the LLM/idle values at translate time, so most changes take effect
immediately without restarting the app.

Values are validated/clamped on write, so a hand-edited or stale file can never
push an out-of-range value into the engines.
"""

import json
import os
import threading

CONFIG_DIR = os.path.expanduser("~/.config/auto-translator")
CONFIG_PATH = os.path.join(CONFIG_DIR, "settings.json")

# key -> (default, kind, min, max) ; kind in {bool,int,float,choice}
_SPEC = {
    "theme":           ("auto", "choice", ("auto", "dark", "light")),
    "auto_translate":  (True,   "bool"),
    "debounce_ms":     (350,    "int",   50,   5000),
    "font_size":       (21,     "int",   12,   40),
    "temperature":     (0.2,    "float", 0.0,  1.5),
    "max_tokens":      (0,      "int",   0,    4096),   # 0 = auto (scale w/ input)
    "idle_unload_sec": (300,    "int",   0,    86400),  # 0 = never auto-unload
}

DEFAULTS = {k: v[0] for k, v in _SPEC.items()}

_lock = threading.Lock()
_current = dict(DEFAULTS)


def _coerce(key, value):
    """Validate/clamp one value against its spec. Returns the accepted value, or
    the current value if it can't be coerced (never raises)."""
    spec = _SPEC.get(key)
    if spec is None:
        return _current.get(key)
    kind = spec[1]
    try:
        if kind == "bool":
            return bool(value)
        if kind == "choice":
            return value if value in spec[2] else _current.get(key, spec[0])
        if kind == "int":
            return max(spec[2], min(spec[3], int(value)))
        if kind == "float":
            return max(spec[2], min(spec[3], float(value)))
    except (TypeError, ValueError):
        return _current.get(key, spec[0])
    return _current.get(key, spec[0])


def load():
    """Load settings from disk into memory (called once at import)."""
    global _current
    merged = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            saved = json.load(f)
        for k in _SPEC:
            if k in saved:
                merged[k] = saved[k]
    except (OSError, ValueError):
        pass
    with _lock:
        _current = {k: _coerce(k, v) for k, v in merged.items()}
    return dict(_current)


def get():
    """A copy of the current settings."""
    with _lock:
        return dict(_current)


def update(patch):
    """Merge a (partial) patch of known keys, clamp, persist, return the result.
    Unknown keys are ignored."""
    global _current
    with _lock:
        for k, v in (patch or {}).items():
            if k in _SPEC:
                _current[k] = _coerce(k, v)
        result = dict(_current)
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # a read-only home shouldn't break the running app
    return result


# ---- typed accessors used by the engines -----------------------------------
def temperature():
    return float(get()["temperature"])


def max_tokens(auto):
    """Token cap for a translation: the user's value, or `auto` when set to 0."""
    v = int(get()["max_tokens"])
    return v if v > 0 else auto


def idle_unload_sec():
    return int(get()["idle_unload_sec"])


load()
