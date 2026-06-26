"""Argos Translate engine — offline NMT, CPU-only, the default.

Language packages (~100-200 MB each) are installed on demand. Direct pairs
are preferred; otherwise we pivot through English (X->en, en->Y), which is
how Argos itself bridges uncommon pairs.
"""

import threading

NAME = "argos"
LABEL = "Argos Translate (offline NMT)"

_lock = threading.Lock()
_index_updated = False  # only hit the network for the package index once


def is_available():
    try:
        import argostranslate.translate  # noqa: F401
        return True
    except Exception:
        return False


def unavailable_reason():
    try:
        import argostranslate.translate  # noqa: F401
        return None
    except Exception as e:
        return (
            "argostranslate が読み込めません。`uv sync` を実行してください。"
            f"（詳細: {type(e).__name__}: {e}）"
        )


def _installed_pair(from_code, to_code):
    import argostranslate.package as pkg
    for p in pkg.get_installed_packages():
        if p.from_code == from_code and p.to_code == to_code:
            return True
    return False


def _install_pair(from_code, to_code, on_status):
    """Install a single language package if not already present.

    Returns True if the pair is available after the call.
    """
    global _index_updated
    import argostranslate.package as pkg

    if from_code == to_code:
        return True
    if _installed_pair(from_code, to_code):
        return True

    if not _index_updated:
        if on_status:
            on_status("パッケージ一覧を取得中…")
        pkg.update_package_index()
        _index_updated = True

    available = pkg.get_available_packages()
    match = next(
        (p for p in available if p.from_code == from_code and p.to_code == to_code),
        None,
    )
    if not match:
        return False
    if on_status:
        on_status(f"言語モデルをダウンロード中 ({from_code}→{to_code})…")
    match.install()
    return True


def _ensure(from_code, to_code, on_status):
    """Make a from->to path available, pivoting through English if needed."""
    if from_code == to_code:
        return True
    if _install_pair(from_code, to_code, on_status):
        return True
    # Pivot through English.
    ok_a = _install_pair(from_code, "en", on_status)
    ok_b = _install_pair("en", to_code, on_status)
    return ok_a and ok_b


def translate(text, src, tgt, on_status=None):
    import argostranslate.translate as t

    if not text.strip():
        return ""
    with _lock:  # Argos package install/translate is not reentrant-friendly
        if not _ensure(src, tgt, on_status):
            raise RuntimeError(
                f"この言語ペアのモデルが見つかりません ({src}→{tgt})。"
            )
        return t.translate(text, src, tgt)
