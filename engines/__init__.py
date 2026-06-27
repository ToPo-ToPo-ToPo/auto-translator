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
    "mlx_engine",
    "mlx_e4b_engine",
]

_cache = {}


def _load(mod_name):
    if mod_name not in _cache:
        _cache[mod_name] = import_module(f"engines.{mod_name}")
    return _cache[mod_name]


def _applicable(mod):
    """Whether an engine applies to the current OS/arch (default: yes)."""
    fn = getattr(mod, "is_applicable", None)
    if not fn:
        return True
    try:
        return bool(fn())
    except Exception:
        return True


def list_engines():
    """Return [{name, label, available, reason?}] for engines that apply to this
    OS. Platform-specific engines (e.g. MLX on non-Apple-Silicon) are omitted."""
    out = []
    for mod_name in _ENGINE_MODULES:
        try:
            mod = _load(mod_name)
            if not _applicable(mod):
                continue
            avail = bool(mod.is_available())
            entry = {"name": mod.NAME, "label": mod.LABEL, "available": avail}
            if not avail:
                entry["reason"] = _reason(mod) or "利用できません。"
            out.append(entry)
        except Exception as e:  # a broken/optional engine shouldn't kill the list
            out.append(
                {"name": mod_name, "label": mod_name, "available": False,
                 "reason": f"{type(e).__name__}: {e}"}
            )
    return out


def _reason(mod):
    fn = getattr(mod, "unavailable_reason", None)
    if not fn:
        return None
    try:
        return fn()
    except Exception:
        return None


def get_engine(name):
    for mod_name in _ENGINE_MODULES:
        mod = _load(mod_name)
        if getattr(mod, "NAME", None) == name:
            return mod
    raise KeyError(f"unknown engine: {name}")


def default_engine_name():
    listed = list_engines()
    for e in listed:
        if e["available"]:
            return e["name"]
    # Fall back to the first listed engine's NAME (not the module name).
    return listed[0]["name"] if listed else "argos"
