# auto-translator

🌐 日本語: **[README.md](README.md)** ・ 📖 Docs: **[docs/](docs/)** (Japanese)

- A standalone, offline desktop translation app. 
- Type into the window and it translates instantly. 
- No external API, no account, no browser.

## Quick start (macOS)

```bash
brew install uv        # if not installed (https://docs.astral.sh/uv/)
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
```

Then **double-click `auto-translator.app`** in the cloned folder. The first launch
sets itself up and opens a standalone window; type and it translates.

> **Windows / Linux** are experimental (no one-click launcher, untested).
> See [docs/installation.md](docs/installation.md).

## Engines

- **Default: Argos Translate** — light, instant, fully offline.
- **Optional: Gemma 4 (MLX / Apple Silicon)** — switchable in the UI; higher
  quality; asks before downloading on first use.

## Documentation

See **[docs/](docs/)** for installation & placement, usage, engines/models &
configuration, troubleshooting (incl. Japanese IME), uninstall, and development.
Release history is in the **[CHANGELOG](CHANGELOG.md)**.

## License

[MIT](LICENSE). Translation models (Argos / Gemma, etc.) follow their own licenses
(Gemma derivatives: [Gemma Terms](https://ai.google.dev/gemma/terms)).
