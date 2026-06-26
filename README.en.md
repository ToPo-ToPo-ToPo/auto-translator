# auto-translator

🌐 日本語版: **[README.md](README.md)**

A small, **standalone, offline** translation app — a local alternative to
DeepL. Type into a browser UI and it translates instantly. No external API, no
account, no internet required after the first model download.

- **Engine: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  purpose-built translation models, CPU-only, ~100–200 MB per language pair.
  Best quality-per-compute and fully offline.
- **GUI:** a local web page served by Python's standard library. Translates as
  you type (auto-detect source).

## Install & launch (macOS)

Install [uv](https://docs.astral.sh/uv/) once (`brew install uv`), then:

```bash
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
```

**Double-click `auto-translator.app`** in the cloned folder — that's the only
step. It sets itself up on first launch (a few seconds), starts the local
server, and opens the translator in your browser. Clicking it again just
re-focuses the tab (it won't start a second copy).

- **To quit:** right-click its Dock icon → **Quit** (this stops the server).
- Setup details are logged to `app.log`.

> Not on macOS? Run it from a terminal instead: `uv run python app.py`.

The first translation for a new language pair downloads its Argos model
(progress shows in the status line). After that it's fully offline.

## Putting it in the Dock / Applications

The `.app` is just a **launcher**; the real app is the cloned **project folder**
(where `app.py` and `.venv` live).

- **Add to the Dock:** drag `auto-translator.app` onto the Dock. The file isn't
  moved — only a reference (shortcut) is created. No copy needed.
- **Add to /Applications:** **⌥(option)-drag to copy** it into `/Applications`
  (a plain drag *moves* it). The launcher still finds the project folder via its
  fallback path.
- ⚠️ **Keep the project folder.** If you delete or move it, the copy you placed
  in `/Applications` stops working (the `.app` is the remote, the project folder
  is the device).
- **Recommended:** leave the `.app` in the project folder and drag *that* to the
  Dock — the launcher and its project stay in sync, with no duplication.
- **Relocating the whole folder:** after moving it, edit the fallback path inside
  the launcher (`auto-translator.app/Contents/MacOS/launch`, currently
  `/path/to/auto-translator`) so the `/Applications`
  copy follows along.

> Note: launching the app never auto-moves it to /Applications — it stays where
> you put it.

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `AUTO_TRANSLATE_HOST` | `127.0.0.1` | Bind host |
| `AUTO_TRANSLATE_PORT` | `8765` | Port |

## How it fits together

```
auto-translator.app   double-clickable macOS launcher (uv sync + uv run app.py)
pyproject.toml        deps (argostranslate / langdetect), managed by uv
app.py                stdlib HTTP server: /api/config, /api/translate, serves web/
web/index.html        the UI (vanilla JS, debounced auto-translate)
engines/              pluggable backends (currently argos only), lazily imported
languages.py          language list + code normalization
```

Adding an engine = drop a module in `engines/` exposing `NAME`, `LABEL`,
`is_available()`, and `translate(text, src, tgt, on_status=None)`, then list it
in `engines/__init__.py`.

## Uninstall

A script removes everything this app created (it never touches unrelated files):

```bash
./uninstall.sh                # venv, logs, caches, Argos language models
./uninstall.sh --keep-models  # keep the downloaded Argos models
./uninstall.sh --yes          # skip the confirmation prompt
```

It lists each target with its size and asks before deleting. To finish, drag the
app out of the Dock and delete the project folder.

## Why Argos instead of a general LLM?

For "small, low compute, standalone," a dedicated NMT model beats a tiny general
LLM on quality-per-FLOP and runs comfortably on CPU (small LLMs tend to need
several GB of RAM and a large model download). So this app sticks with Argos.
