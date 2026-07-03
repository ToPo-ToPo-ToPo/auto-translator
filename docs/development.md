# 開発・自作モデル

## 構成

```
auto-translator.app   ダブルクリック起動の macOS ランチャー（uv sync + uv run app.py）
pyproject.toml        依存定義（argostranslate / langdetect / pywebview / mlx-vlm、llamacppはextra）
app.py                ローカルHTTPサーバ（/api/config, /api/translate, /api/logs）+ ウインドウ起動
web/index.html        UI（素のJS。入力連動の自動翻訳、ログパネル）
engines/              プラガブルなバックエンド（argos / mlx / mlx-e4b / llamacpp）。遅延import
tools/build_mlx_model.py  公式重みからローカルMLXモデルを変換（e2b/e4b/all）
languages.py          言語リストとコード正規化
detection.py          言語自動検出（スクリプト判定 + langdetect。決定的・対応言語に限定）
```

UIはローカルWebView（macOSは WKWebView）でHTML/JSを表示し、裏でPythonサーバが
エンジンを実行する**ハイブリッドのデスクトップアプリ**です。

## エンジンの追加

`engines/` に以下を持つモジュールを置き、`engines/__init__.py` の `_ENGINE_MODULES`
に登録するだけです（先頭が既定）。

- `NAME` / `LABEL`
- `is_available() -> bool`
- `translate(text, src, tgt, on_status=None) -> str`
- 任意: `unavailable_reason()`, `is_applicable()`（OS限定時）, `pending_download()`（DL確認用）

## MLXモデルを自分で変換する（任意）

通常は公開HFリポジトリから自動DLされますが、オフラインで自前ビルドもできます。
変換と読み込みは**同じ mlx-vlm 0.6.3**で行う必要があるため、本アプリはこの版に固定
しています（公式重みは experts が fused 形式のため、特別なパッチは不要）。

```bash
uv run python tools/build_mlx_model.py e2b   # ~9.5GB DL → 約3.3GB
uv run python tools/build_mlx_model.py e4b   # ~16GB DL → 約5GB
```

出力は `~/.cache/auto-translator/mlx/` に保存され、HF版より優先して使われます。

## MTP（高速化 / speculative decoding）

Gemma 4 は公式の **`-assistant` ドラフター**を使った Multi-Token Prediction で
高速化できます（ロスレス）。ドラフターは mlx-vlm でそのままロードできます。

```python
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

model, processor = load("ToPo-ToPo/gemma-4-26B-A4B-it-mlx-4bit")
draft_model, _   = load("google/gemma-4-26b-a4b-it-assistant")
config = load_config("ToPo-ToPo/gemma-4-26B-A4B-it-mlx-4bit")
prompt = apply_chat_template(processor, config, "...", num_images=0)
out = generate(model, processor, prompt, draft_model=draft_model, draft_kind="mtp")
```

- `draft_kind="mtp"` が必須（CLI `mlx_vlm.generate --draft-model ...` は自動判定）。
- ドラフターはサイズ一致が必要（26B用は26B本体のみ。E2B/E4Bは各自の `-assistant`）。
- mlx-vlm 0.6.3 以上。出力は非MTPと一致（一致しなければ版の不整合）。

## 公開モデル（自作・MLX）

[Hugging Face: ToPo-ToPo](https://huggingface.co/ToPo-ToPo) に公開。アプリが使うのは
主に Gemma 4 E2B/E4B です。

- `gemma-4-E2B-it-qat-mlx-4bit` / `gemma-4-E4B-it-qat-mlx-4bit`（アプリ既定の任意LLM）
- `gemma-4-26B-A4B-it-mlx-{bf16,8bit,4bit}` ほか（大型・MTP説明付き）

## なぜ Argos が既定か

「小さい・低計算コスト・即時・オフライン」を満たすため、翻訳専用NMT（Argos）を
既定にしています。文脈やニュアンスで上を狙いたいときに MLX（Gemma 4）へ切り替える、
という使い分けです。
