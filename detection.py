"""Language auto-detection tuned for this app.

Plain `langdetect.detect()` has problems that showed up in real use:
  * No seed -> non-deterministic: the same text can flip between languages
    across keystrokes ("Hello" alternates fi/no).
  * Kanji-only Japanese is mis-detected (東京駅 -> ko, 日本語 -> zh-tw).
  * It can return languages the app doesn't support (tl, af, so...), which then
    fail downstream as an unknown translation pair.
  * The profile factory loads lazily on the first call, which both delays the
    first translation and races when two requests arrive at once.

Fixes here:
  * Unicode-script fast paths decide unambiguous scripts (kana, hangul, Thai,
    Devanagari, Arabic, Han) without touching langdetect at all — fast and
    deterministic for the most commonly mixed-up cases.
  * langdetect runs with a fixed seed, is initialised once behind a lock, and
    its ranked candidates are filtered to the languages the app supports.
  * Results are memoised and only the first ~1200 chars are examined —
    detection accuracy plateaus long before that, so huge pastes stay cheap.
"""

import re
import threading
from functools import lru_cache

from languages import LANGUAGES, normalize_code

SUPPORTED = {code for code, _, _ in LANGUAGES}

_SAMPLE_LEN = 1200   # detection gains nothing beyond this; keeps big pastes cheap

# Scripts that identify a supported language on their own. Checked in order —
# kana must come before Han so mixed Japanese (kanji+kana) resolves to ja.
_SCRIPT_HINTS = (
    ("ja", re.compile(r"[぀-ヿ]")),                       # hiragana/katakana
    ("ko", re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]")),  # hangul
    ("th", re.compile(r"[฀-๿]")),
    ("hi", re.compile(r"[ऀ-ॿ]")),                       # devanagari
    ("ar", re.compile(r"[؀-ۿݐ-ݿ]")),
)
_HAN = re.compile(r"[㐀-䶿一-鿿]")

# Shinjitai that exist ONLY in Japanese — the post-war simplifications differ
# from both simplified and traditional Chinese (駅 vs 驛/驿, 経 vs 經/经, ...).
# Any of these in kana-less text is decisive for Japanese; without them,
# kanji-only strings like 東京駅-less 日本語 are genuinely ambiguous with
# Chinese and default to zh.
_JA_ONLY_KANJI = frozenset(
    "駅訳沢択実変売続読発経済剤円図広検険験帰桜労単団弾対帯気芸県児専戦銭総"
    "蔵臓転伝悩脳廃拝髪抜仏塩縁応穏価絵拡覚楽観関顔挙郷駆恵継鶏撃権顕厳黒歯"
    "釈収従渋獣縦処焼証乗浄剰畳縄譲醸粋酔髄摂繊荘騒滝遅鋳庁聴鉄稲闘弐覇浜払"
    "歩豊毎満黙薬揺様謡頼覧竜両猟緑涙塁戻霊齢暦歴録亀悪圧囲壱隠栄営壊懐渇巻"
    "陥勧寛歓戯犠拠暁蛍軽倹剣圏砕斎雑桟賛徳効"
)


def _script_hint(sample):
    """Resolve languages that a Unicode script identifies unambiguously.
    Returns a code or None (None = let the statistical detector decide)."""
    for code, rx in _SCRIPT_HINTS:
        if rx.search(sample):
            return code
    # Han with no kana: Japanese if a Japan-only glyph appears, else Chinese.
    # Require a meaningful share so a lone CJK character inside Latin text
    # doesn't flip the whole detection.
    han = len(_HAN.findall(sample))
    if han and han / max(1, len(sample.replace(" ", ""))) >= 0.25:
        if any(c in _JA_ONLY_KANJI for c in sample):
            return "ja"
        return "zh"
    return None


# ---- langdetect, initialised once and deterministically ---------------------
_init_lock = threading.Lock()
_factory_ready = False


def _ensure_factory():
    """Load langdetect's profiles exactly once (they're not thread-safe to
    initialise concurrently) with a fixed seed for reproducible results."""
    global _factory_ready
    if _factory_ready:
        return
    with _init_lock:
        if _factory_ready:
            return
        from langdetect import DetectorFactory
        from langdetect.detector_factory import init_factory
        DetectorFactory.seed = 0
        init_factory()
        _factory_ready = True


def prewarm():
    """Load the detector in the background at startup so the first translation
    doesn't pay the profile-loading cost (and can't race another request)."""
    threading.Thread(target=lambda: _try(_ensure_factory),
                     name="detect-prewarm", daemon=True).start()


def _try(fn):
    try:
        fn()
    except Exception:
        pass


@lru_cache(maxsize=256)
def _detect_sample(sample):
    hint = _script_hint(sample)
    if hint:
        return hint

    candidates = []
    try:
        _ensure_factory()
        from langdetect import detect_langs
        candidates = detect_langs(sample)
    except Exception:
        pass
    # Best-ranked candidate the app actually supports (fixes e.g. Привет мир ->
    # bg:0.72/ru:0.28 by skipping the unsupported bg).
    for c in candidates:
        code = normalize_code(c.lang)
        if code in SUPPORTED:
            return code
    # No supported candidate. Short ASCII text is why this happens in practice
    # ("Hello" -> fi/no, "OK thanks" edge cases) — call it English rather than
    # returning something the engines can't translate from.
    if sample.isascii():
        return "en"
    return None


def detect(text):
    """Best-effort language detection. Returns a supported ISO code or None."""
    text = (text or "").strip()
    if not text:
        return None
    return _detect_sample(text[:_SAMPLE_LEN])
