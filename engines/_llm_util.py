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
        f'Reply with ONLY a JSON array of strings, e.g. ["...", "..."]. '
        f"Do not repeat the original wording and add no explanations."
    )


def parse_alternatives(raw, selection, limit=6):
    """Turn a model reply into a de-duplicated list of suggestions.

    Prefers a JSON array if one is present; otherwise falls back to splitting on
    newlines/commas and stripping bullets/quotes. The original selection and any
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
        key = it.lower()
        if not it or key == sel or key in seen:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= limit:
            break
    return out
