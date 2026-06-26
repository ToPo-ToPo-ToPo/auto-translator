# auto-translator

🌐 日本語版: **[README.md](README.md)**

A small, **standalone, offline-first** translation app — a local alternative to
DeepL. Type into a browser UI and it translates instantly. No external API, no
account, no internet required after the first model download.

- **Default engine: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  purpose-built translation models, CPU-only, ~100–200 MB per language pair.
  Best quality-per-compute and fully offline.
- **Optional small-LLM engines** (Gemma 4 E-series), switchable in the UI:
  - **MLX** — Gemma 4 **E2B** by default (E4B for higher quality) on Apple Silicon.
  - **llama.cpp** — any small Gemma 4 GGUF.
- **GUI:** a local web page served by Python's standard library — nothing to
  install beyond the engine. Translates as you type (auto-detect source).

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
- **MLX (Gemma 4 E2B)** installs automatically on Apple Silicon; pick it in the
  engine dropdown (weights download on first use).

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

## Small-LLM backends

**MLX (Gemma 4) is installed automatically on Apple Silicon macOS** — just pick
it in the engine dropdown (the model weights download on first use). On other
platforms it is skipped. To choose a different MLX model:

```bash
# step up to E4B (better quality) or down to a 4-bit build (less RAM)
export AUTO_TRANSLATE_MLX_MODEL=Rapid42/gemma-4-E4B-it-MLX
# export AUTO_TRANSLATE_MLX_MODEL=unsloth/gemma-4-E2B-it-UD-MLX-4bit
```

The llama.cpp engine is opt-in (it needs a GGUF file):

```bash
uv sync --extra llamacpp
export AUTO_TRANSLATE_GGUF=/path/to/gemma-4-E2B-it.gguf
```

Restart the app; the engine dropdown will offer the newly available backends.

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `AUTO_TRANSLATE_HOST` | `127.0.0.1` | Bind host |
| `AUTO_TRANSLATE_PORT` | `8765` | Port |
| `AUTO_TRANSLATE_MLX_MODEL` | `Rapid42/gemma-4-E2B-it-MLX` | MLX model id (Gemma 4 E2B/E4B) |
| `AUTO_TRANSLATE_GGUF` | _(unset)_ | Path to a GGUF for the llama.cpp engine |

## How it fits together

```
auto-translator.app   double-clickable macOS launcher (uv sync + uv run app.py)
pyproject.toml        deps (auto MLX on Apple Silicon; llamacpp extra), via uv
app.py                stdlib HTTP server: /api/config, /api/translate, serves web/
web/index.html        the UI (vanilla JS, debounced auto-translate)
engines/              pluggable backends (argos / mlx / llamacpp), lazily imported
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
./uninstall.sh --all          # also remove this app's Gemma 4 LLM downloads
./uninstall.sh --yes          # skip the confirmation prompt
```

It lists each target with its size and asks before deleting. `--all` only
removes the specific Gemma 4 repos this app downloads (`Rapid42/gemma-4-E2B-it-MLX`
and the documented alternates) — never your other models in the shared
Hugging Face cache. To finish, drag the app out of the Dock and delete the
project folder.

## Why Argos instead of a general LLM by default?

For "small, low compute, standalone," a dedicated NMT model beats a tiny general
LLM on quality-per-FLOP and runs comfortably on CPU. The LLM engines are there
when you want their flexibility — but the default keeps cost low.
