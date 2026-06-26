"""Pluggable translation engines.

Each engine module exposes:
    NAME            : str   - stable id used by the API/UI
    LABEL           : str   - human-readable label
    is_available()  : bool  - whether deps/models are present right now
    translate(text, src, tgt, on_status=None) -> str

Engines are imported lazily. Argos is the only built-in engine; add more by
dropping a module here and listing it in _ENGINE_MODULES.
"""

from importlib import import_module

# In priority order. First available = default (Argos stays the lightweight
# default; llama.cpp is selectable in the UI for higher-quality LLM output).
_ENGINE_MODULES = [
    "argos_engine",
    "llamacpp_engine",
]

_cache = {}


def _load(mod_name):
    if mod_name not in _cache:
        _cache[mod_name] = import_module(f"engines.{mod_name}")
    return _cache[mod_name]


def list_engines():
    """Return [{name, label, available}] for every known engine."""
    out = []
    for mod_name in _ENGINE_MODULES:
        try:
            mod = _load(mod_name)
            out.append(
                {
                    "name": mod.NAME,
                    "label": mod.LABEL,
                    "available": bool(mod.is_available()),
                }
            )
        except Exception as e:  # a broken/optional engine shouldn't kill the list
            out.append(
                {"name": mod_name, "label": mod_name, "available": False, "error": str(e)}
            )
    return out


def get_engine(name):
    for mod_name in _ENGINE_MODULES:
        mod = _load(mod_name)
        if getattr(mod, "NAME", None) == name:
            return mod
    raise KeyError(f"unknown engine: {name}")


def default_engine_name():
    for e in list_engines():
        if e["available"]:
            return e["name"]
    return _ENGINE_MODULES[0]
