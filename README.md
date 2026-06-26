# auto-translator

A small, **standalone, offline-first** translation app — a local alternative to
DeepL. Type into a browser UI and it translates instantly. No external API, no
account, no internet required after the first model download.

- **Default engine: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  purpose-built translation models, CPU-only, ~100–200 MB per language pair.
  Best quality-per-compute and fully offline.
- **Optional small-LLM engines** (Gemma 4 E-series), switchable in the UI:
  - **MLX** (`mlx-lm`) — Gemma 4 **E2B** by default (E4B for higher quality) on Apple Silicon.
  - **llama.cpp** (`llama-cpp-python`) — any small Gemma 4 GGUF.
- **GUI:** a local web page served by Python's standard library — nothing to
  install beyond the engine. Translates as you type (auto-detect source).

## かんたん導入（日本語）

[uv](https://docs.astral.sh/uv/) が必要です（未インストールなら
`brew install uv`）。

```bash
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
cd auto-translator
./run.sh                 # 依存を準備して起動（ブラウザが自動で開きます）
```

- **アプリとして使う:** Finder で `auto-translator.app` をダブルクリック。
  Dock やアプリケーションフォルダにドラッグしてもOK。終了は Dock アイコンを
  右クリック →「終了」。
- **小型LLM（MLX / Gemma 4 E2B）:** Apple Silicon の Mac では**自動で導入**され、
  UIのエンジン欄に出ます（モデル本体はそのエンジンを初めて選んだ時にDL）。
- **アンインストール:** `./uninstall.sh`（下記「Uninstall」参照）。

## Quick start (macOS — click to launch)

Double-click **`auto-translator.app`** in Finder. It starts the local server and
opens the translator in your browser. Clicking it again just re-focuses the tab
(it won't start a second copy).

- **Add to Dock / Applications:** drag `auto-translator.app` to the Dock or to
  `/Applications`. It still finds the project even after being moved.
- **To quit:** right-click its Dock icon → **Quit** (this stops the server).
- First launch may take a few seconds if it needs to build the virtual env;
  details are logged to `app.log`.

## Quick start (terminal)

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```bash
cd auto-translator
./run.sh            # uv sync + launch, opens the browser
```

Or manually:

```bash
uv sync                       # create .venv from pyproject.toml / uv.lock
uv run python app.py          # then open http://127.0.0.1:8765
```

The first translation for a new language pair downloads its Argos model
(progress shows in the status line). After that it's fully offline.

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
uv sync --extra llamacpp     # or: ./run.sh --llamacpp
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
```
