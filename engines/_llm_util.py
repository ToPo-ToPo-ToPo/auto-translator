"""Helpers shared by the LLM engines for the translation post-edit feature.

When the user double-clicks a word (or selects a phrase) in the translation, the
UI asks the current LLM engine for alternative wordings. These helpers build the
prompt and parse the model's reply into a clean, de-duplicated list.
"""

import json
import re

from languages import NAMES


def alt_prompt(sentence, selection, src, tgt):
    """Prompt asking the model to reword `selection` within `sentence`."""
    src_name = "the source language" if src in ("", "auto", None) else NAMES.get(src, src)
    tgt_name = NAMES.get(tgt, tgt)
    return (
        f"You are a bilingual editor. The sentence below is a {tgt_name} "
        f"translation from {src_name}:\n\n{sentence}\n\n"
        f'Suggest up to 6 alternative {tgt_name} wordings for the part "{selection}" '
        f"that keep the sentence natural and preserve its meaning. "
        f"Each suggestion must be a drop-in replacement for ONLY that part "
        f"(a word or short phrase) — never the whole sentence. "
        f'Reply with ONLY a JSON array of strings, e.g. ["...", "..."]. '
        f"Do not repeat the original wording and add no explanations."
    )


def rephrase_prompt(source_text, sentence, selection, replacement, src, tgt):
    """Prompt asking the model to rewrite the whole translation so it uses the
    replacement the user picked, adjusting the surrounding words to match
    (DeepL-style: choosing a word re-flows the rest of the sentence)."""
    src_name = "the source language" if src in ("", "auto", None) else NAMES.get(src, src)
    tgt_name = NAMES.get(tgt, tgt)
    parts = []
    if (source_text or "").strip():
        parts.append(f"Source text ({src_name}):\n{source_text}\n")
    parts.append(f"Current {tgt_name} translation:\n{sentence}\n")
    parts.append(
        f'The user replaced "{selection}" with "{replacement}" in the translation. '
        f'Rewrite the whole {tgt_name} translation so that it uses "{replacement}" '
        f"and reads naturally. The replacement may have made surrounding words "
        f"redundant, ungrammatical or awkward — smooth all of that out: adjust "
        f"grammar, particles, agreement, collocations and remove any redundancy, "
        f"while staying faithful to the source meaning. Do not change parts that "
        f"already read naturally. "
        f"Output ONLY the revised translation, with no explanations or quotes."
    )
    return "\n".join(parts)


def parse_rephrase(raw, fallback):
    """Clean a rewritten-translation reply: drop code fences / surrounding
    quotes / lead-ins like "Revised translation:". Returns `fallback` (the
    locally-substituted sentence) if the model returned nothing usable."""
    text = (raw or "").strip()
    m = re.search(r"```(?:\w+)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1).strip()
    text = re.sub(r"^(?:revised|corrected|updated)?\s*translation\s*[:：]\s*",
                  "", text, flags=re.I)
    if len(text) >= 2 and text[0] in "\"'「『“" and text[-1] in "\"'」』”":
        text = text[1:-1].strip()
    return text or fallback


def _extract_core(candidate, sentence):
    """The model sometimes ignores instructions and returns the whole sentence
    with the replacement applied. Recover just the replacement by stripping the
    prefix and suffix the candidate shares with the original sentence."""
    a, b = sentence, candidate

    def _mid_word(x, y):
        # Both sides of a cut are Latin word chars -> we'd split mid-word
        # ("change"/"move" share a trailing "e"). CJK has no spaces; leave it.
        return x.isascii() and x.isalnum() and y.isascii() and y.isalnum()

    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    while i > 0 and i < len(b) and _mid_word(b[i - 1], b[i]):
        i -= 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    while j > 0 and _mid_word(b[len(b) - j - 1], b[len(b) - j]):
        j -= 1
    return b[i:len(b) - j].strip()


def parse_alternatives(raw, selection, limit=6, sentence=""):
    """Turn a model reply into a de-duplicated list of suggestions.

    Prefers a JSON array if one is present; otherwise falls back to splitting on
    newlines/commas and stripping bullets/quotes. Full-sentence replies are
    reduced to the part that actually changed. The original selection and any
    duplicates (case-insensitive) are dropped."""
    raw = (raw or "").strip()
    items = []

    m = re.search(r"\[.*\]", raw, re.S)
    if m:
        try:
            items = [str(x) for x in json.loads(m.group(0))]
        except Exception:
            items = []
    if not items:
        for part in re.split(r"[\n,]+", raw):
            items.append(part)

    out, seen = [], set()
    sel = (selection or "").strip().lower()
    for it in items:
        it = it.strip().strip("-*•").strip().strip('"').strip("'").strip()
        # A candidate much longer than the selection is a whole-sentence reply,
        # not a drop-in replacement — reduce it to the changed part.
        if sentence and it and len(it) > len(selection) * 3 + 9:
            it = _extract_core(it, sentence)
            if not it or len(it) > len(selection) * 4 + 12:
                continue
        key = it.lower()
        if not it or key == sel or key in seen:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= limit:
            break
    return out
