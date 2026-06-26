"""Shared language metadata used by all engines and the web UI.

Codes are ISO 639-1, which is what Argos Translate uses. The LLM engines
get the human-readable name (better for prompting) via NAMES.
"""

# Common languages. Add more freely — Argos supports many of these and the
# LLM engines accept any name. (code, English name, native label)
LANGUAGES = [
    ("en", "English", "English"),
    ("ja", "Japanese", "日本語"),
    ("zh", "Chinese", "中文"),
    ("ko", "Korean", "한국어"),
    ("es", "Spanish", "Español"),
    ("fr", "French", "Français"),
    ("de", "German", "Deutsch"),
    ("it", "Italian", "Italiano"),
    ("pt", "Portuguese", "Português"),
    ("ru", "Russian", "Русский"),
    ("ar", "Arabic", "العربية"),
    ("hi", "Hindi", "हिन्दी"),
    ("nl", "Dutch", "Nederlands"),
    ("pl", "Polish", "Polski"),
    ("tr", "Turkish", "Türkçe"),
    ("vi", "Vietnamese", "Tiếng Việt"),
    ("th", "Thai", "ไทย"),
    ("id", "Indonesian", "Bahasa Indonesia"),
    ("uk", "Ukrainian", "Українська"),
    ("cs", "Czech", "Čeština"),
    ("sv", "Swedish", "Svenska"),
]

NAMES = {code: name for code, name, _ in LANGUAGES}

# Map of detector output -> our codes, for langdetect quirks (e.g. zh-cn).
_DETECT_FIXUP = {
    "zh-cn": "zh",
    "zh-tw": "zh",
    "zh-hans": "zh",
    "zh-hant": "zh",
}


def normalize_code(code: str) -> str:
    code = (code or "").lower()
    return _DETECT_FIXUP.get(code, code.split("-")[0])
