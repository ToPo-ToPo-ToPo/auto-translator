# auto-translator

🌐 日本語版: **[README.md](README.md)**

A small, **standalone, offline** translation app — a local alternative to
DeepL. Type into a browser UI and it translates instantly. No external API, no
account, no internet required after the first model download.

- **Default engine: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  purpose-built translation models, CPU-only, ~100–200 MB per language pair.
  Best quality-per-compute and fully offline.
- **Optional small-LLM engine: llama.cpp (Gemma 4)** — switchable in the UI. One
  GGUF runs the same on Apple Silicon (Metal), Intel, Linux and Windows. Default
  model is Gemma 4 E2B (auto-downloaded on first use).
- **Optional small-LLM engine: MLX (Gemma 4 E2B)** — Apple Silicon only. Uses a
  local MLX model you convert yourself from the official weights (not published);
  build it once with `tools/build_mlx_model.py`.
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

## Small-LLM engine (llama.cpp, optional)

Pick **"Gemma 4 E2B (llama.cpp)"** in the engine dropdown to switch to LLM
translation. Argos stays the default, so you only pay for the LLM when you want
it.

- On **first selection** it auto-downloads the default model (Gemma 4 E2B Q4_0,
  ~3.35 GB); offline afterwards. Memory use is roughly **~4 GB** (~5.5 GB for E4B).
- **Swap the model** via env vars:

```bash
# use an existing local GGUF (highest priority, no download)
export AUTO_TRANSLATE_GGUF=/path/to/model.gguf

# or point at a different HF repo/file (e.g. E4B for higher quality, more RAM)
export AUTO_TRANSLATE_GGUF_REPO=google/gemma-4-E4B-it-qat-q4_0-gguf
export AUTO_TRANSLATE_GGUF_FILE=gemma-4-E4B_q4_0-it.gguf
```

GGUFs are stored under `~/.cache/huggingface`; delete them manually if unwanted.

## Small-LLM engine (MLX, Apple Silicon, optional)

This engine runs a **local MLX model you convert yourself** from the official
weights (nothing is published). MLX runs efficiently on Apple Silicon.

```bash
# one-time: convert the official weights to MLX 4-bit (~9.5 GB download -> ~3.3 GB)
uv run python tools/build_mlx_model.py
```

Afterwards **"Gemma 4 E2B (MLX)"** appears in the engine menu (~4–5 GB RAM).
Until it's built, the UI shows a clear "not built yet" reason. Conversion and
loading must use the **same mlx-vlm (0.6.3)**, so the app pins that version.

- The model lives under `~/.cache/auto-translator/mlx/` (removed by uninstall).
- `AUTO_TRANSLATE_MLX_MODEL` overrides the local path (or an HF repo id).

## Configuration (env vars)

| Variable | Default | Purpose |
|---|---|---|
| `AUTO_TRANSLATE_HOST` | `127.0.0.1` | Bind host |
| `AUTO_TRANSLATE_PORT` | `8765` | Port |
| `AUTO_TRANSLATE_GGUF` | _(unset)_ | Local GGUF path for llama.cpp (highest priority) |
| `AUTO_TRANSLATE_GGUF_REPO` | `google/gemma-4-E2B-it-qat-q4_0-gguf` | HF repo to auto-download |
| `AUTO_TRANSLATE_GGUF_FILE` | `gemma-4-E2B_q4_0-it.gguf` | GGUF filename within the repo |
| `AUTO_TRANSLATE_MLX_MODEL` | `~/.cache/auto-translator/mlx/gemma-4-E2B-it-qat-mlx-4bit` | MLX model local path (or HF repo id) |

## How it fits together

```
auto-translator.app   double-clickable macOS launcher (uv sync + uv run app.py)
pyproject.toml        deps (argostranslate / langdetect / llama-cpp-python / mlx-vlm)
app.py                stdlib HTTP server: /api/config, /api/translate, serves web/
web/index.html        the UI (vanilla JS, debounced auto-translate)
engines/              pluggable backends (argos / llamacpp / mlx), lazily imported
tools/build_mlx_model.py  convert the local MLX model from official weights (Apple Silicon)
languages.py          language list + code normalization
```

Adding an engine = drop a module in `engines/` exposing `NAME`, `LABEL`,
`is_available()`, and `translate(text, src, tgt, on_status=None)`, then list it
in `engines/__init__.py`.

## Uninstall

A script removes everything this app created (it never touches unrelated files):

```bash
./uninstall.sh                # venv, logs, caches, Argos models, local MLX model
./uninstall.sh --keep-models  # keep downloaded/built models
./uninstall.sh --yes          # skip the confirmation prompt
```

It lists each target with its size and asks before deleting. To finish, drag the
app out of the Dock and delete the project folder.

## Why Argos is the default

For "small, low compute, standalone," a dedicated NMT model (Argos) beats a tiny
general LLM on quality-per-FLOP and runs instantly on CPU. LLMs are stronger on
context and nuance, so the llama.cpp (Gemma 4) engine is there **when you want
higher quality** — at the cost of several GB of RAM and a first-use download.
Light Argos by default, LLM on demand.
