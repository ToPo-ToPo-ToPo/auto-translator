# auto-translator

🌐 English version: **[README.en.md](README.en.md)**

DeepL の代わりになる、**単独動作・オフライン**のローカル翻訳アプリです。
単体アプリのウインドウに文章を入力すると即時に翻訳します。外部API・アカウント不要で、
最初のモデルDL後はインターネットも不要です。

- **既定エンジン（macOS / Apple Silicon）: MLX Gemma 4 E2B** — 高速・高品質。
  公開済みの [`ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit`](https://huggingface.co/ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit)
  を**初回利用時に自動DL**（約3.3GB、以降オフライン）。E4B も選択可。
- **既定エンジン（その他OS）: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  翻訳専用NMT。CPUのみ・1ペア約100〜200MB・低計算コストで完全オフライン。
  （macOSでもUIで選択可）
- **任意: llama.cpp（Gemma 4 GGUF）** — 既定では導入しません。使う場合は
  `uv sync --extra llamacpp`（macOSではMLX推奨）。
- **GUI:** ブラウザ不要の**単体アプリウインドウ**（pywebview / macOSは WKWebView）。
  入力するそばから翻訳します（原文の言語は自動検出）。

## インストールと起動（macOS）

事前に [uv](https://docs.astral.sh/uv/) を入れておきます（未導入なら
`brew install uv`）。

```bash
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
```

あとは clone したフォルダ内の **`auto-translator.app` をダブルクリックするだけ**です。
初回だけアプリが自動で準備し（数秒〜十数秒）、**単体ウインドウ**が開きます（ブラウザは使いません）。
2回目以降は即起動します（起動中にもう一度クリックしても二重起動しません）。

- **終了:** ウインドウを閉じる（または Dock アイコン右クリック →「終了」）。
- 準備の詳細は `app.log` に記録されます。

> macOS 以外の場合: ターミナルから `uv run python app.py` で起動できます。

最初の言語ペアだけ Argos のモデルを自動DLします（進捗はステータス行に表示）。
以降は完全オフラインです。

## Dock / アプリケーションフォルダに置く

`.app` は**起動役（ランチャー）**で、本体は clone した**プロジェクトフォルダ**
（`app.py` や `.venv` がある場所）です。この関係を踏まえて配置します。

- **Dock に入れる:** `auto-translator.app` を Dock にドラッグするだけ。ファイルは
  移動せず、**参照（ショートカット）だけ**が作られます。コピー不要。
- **アプリケーションフォルダに入れる:** `.app` を **⌥(option)を押しながらドラッグ
  ＝コピー**して `/Applications` に置きます（単純ドラッグだと「移動」になります）。
  コピーでも、ランチャーがプロジェクトフォルダを見つけて起動します。
- ⚠️ **プロジェクトフォルダ本体は残してください。** ここを削除・移動すると、
  `/Applications` 等に置いた `.app` も動かなくなります（`.app` はリモコン、
  プロジェクトフォルダが本体というイメージです）。
- **おすすめ:** `.app` はプロジェクトフォルダに置いたまま、それを Dock にドラッグ。
  本体とリモコンが一致して一番分かりやすく、重複も生まれません。
- **フォルダごと引っ越す場合:** プロジェクトフォルダを移動したあと、ランチャー
  （`auto-translator.app/Contents/MacOS/launch`）内のフォールバック用パス
  （現在 `/path/to/auto-translator`）を新しい場所に
  書き換えれば、`/Applications` のコピーも追従します。

> 補足: 起動してもアプリが自動でアプリケーションフォルダへ移動することはありません。
> 置いた場所にそのまま留まります。

## 小型LLMエンジン（llama.cpp / 任意・既定では未導入）

クロスプラットフォーム（Intel/Linux/Windows等）でLLMを使いたい場合の任意エンジンです。
**既定では導入しません**（プリビルトwheelがCPUアーキと不一致になる場合があるため。
macOSでは上記 MLX を推奨）。使うには:

```bash
uv sync --extra llamacpp
```

導入後、UIで **「Gemma 4 E2B (llama.cpp)」** を選択可能になります。

- **初回選択時**に既定モデル（Gemma 4 E2B Q4_0, 約3.35GB）を自動DLします。
  以降はオフライン。使用メモリは概ね **約4GB**（E4Bなら約5.5GB）。
- **モデルの差し替え**（環境変数）:

```bash
# 既存のローカルGGUFを使う（最優先・DLなし）
export AUTO_TRANSLATE_GGUF=/path/to/model.gguf

# 別のHFリポジトリ/ファイルに変える（例: E4B で高品質・要メモリ増）
export AUTO_TRANSLATE_GGUF_REPO=google/gemma-4-E4B-it-qat-q4_0-gguf
export AUTO_TRANSLATE_GGUF_FILE=gemma-4-E4B_q4_0-it.gguf
```

GGUF は `~/.cache/huggingface` に保存されます。不要になったら手動で削除できます。

## 小型LLMエンジン（MLX / Apple Silicon）

macOS（Apple Silicon）の**既定エンジン**です。**初回利用時に公開HFリポジトリから
自動DL**されます（ビルド不要）:
- E2B: `ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit`（約3.3GB / メモリ約4〜5GB・**既定**）
- E4B: `ToPo-ToPo/gemma-4-E4B-it-qat-mlx-4bit`（約5GB / メモリ約6GB・UIで選択）

変換と読み込みは同じ **mlx-vlm 0.6.3** が必要なため、本アプリはこの版に固定しています。

**オフラインで自前ビルドしたい場合**（任意。ローカルにあればHF版より優先使用）:
```bash
uv run python tools/build_mlx_model.py e2b   # ~9.5GB DL→約3.3GB
uv run python tools/build_mlx_model.py e4b   # ~16GB DL→約5GB
```
`AUTO_TRANSLATE_MLX_MODEL` / `AUTO_TRANSLATE_MLX_E4B_MODEL` でローカルパスや別リポに差し替え可。

> **OS自動判定:** MLX は Apple Silicon 専用です。**他のOS / Intel Mac では
> mlx-vlm 自体が導入されず、エンジン一覧にも出ません**（その環境で使えるものだけ自動提示）。
> どのOSでも `argos` は利用可。llama.cpp は任意（`uv sync --extra llamacpp`）。

- モデルは `~/.cache/auto-translator/mlx/` に保存（アンインストールで削除されます）。
- `AUTO_TRANSLATE_MLX_MODEL`（E2B）/ `AUTO_TRANSLATE_MLX_E4B_MODEL`（E4B）で
  ローカルパスや別モデルに差し替え可能。

## 設定（環境変数）

| 変数 | 既定値 | 用途 |
|---|---|---|
| `AUTO_TRANSLATE_HOST` | `127.0.0.1` | バインドするホスト |
| `AUTO_TRANSLATE_PORT` | `8765` | ポート |
| `AUTO_TRANSLATE_GGUF` | _(未設定)_ | llama.cpp 用のローカルGGUFパス（最優先） |
| `AUTO_TRANSLATE_GGUF_REPO` | `google/gemma-4-E2B-it-qat-q4_0-gguf` | 自動DLするHFリポジトリ |
| `AUTO_TRANSLATE_GGUF_FILE` | `gemma-4-E2B_q4_0-it.gguf` | リポジトリ内のGGUFファイル名 |
| `AUTO_TRANSLATE_MLX_MODEL` | `~/.cache/auto-translator/mlx/gemma-4-E2B-it-qat-mlx-4bit` | MLX E2B モデルのローカルパス（or HFリポジトリID） |
| `AUTO_TRANSLATE_MLX_E4B_MODEL` | `~/.cache/auto-translator/mlx/gemma-4-E4B-it-qat-mlx-4bit` | MLX E4B モデルのローカルパス（or HFリポジトリID） |

## 構成

```
auto-translator.app   ダブルクリック起動の macOS ランチャー（uv sync + uv run app.py）
pyproject.toml        依存定義（argostranslate / langdetect / pywebview / mlx-vlm、llamacppはextra）。uv 管理
app.py                標準ライブラリの HTTPサーバ: /api/config, /api/translate, web/ 配信
web/index.html        UI（素のJS、入力に連動した自動翻訳）
engines/              プラガブルなバックエンド（argos / llamacpp / mlx E2B / mlx E4B）。遅延import
tools/build_mlx_model.py  公式重みからローカルMLXモデルを変換（e2b/e4b/all, Apple Silicon）
languages.py          言語リストとコード正規化
```

エンジン追加 = `engines/` に `NAME` / `LABEL` / `is_available()` /
`translate(text, src, tgt, on_status=None)` を持つモジュールを置き、
`engines/__init__.py` に登録するだけ。

## アンインストール

このアプリが作成したものだけを削除するスクリプトです（無関係なファイルには触れません）:

```bash
./uninstall.sh                # venv・ログ・キャッシュ・Argosモデル・ローカルMLXモデル
./uninstall.sh --keep-models  # ダウンロード/作成済みモデルは残す
./uninstall.sh --yes          # 確認プロンプトを省略
```

削除前に対象とサイズを一覧表示し、確認を求めます。最後に、Dock から `.app` を外し、
プロジェクトフォルダを削除すれば完了です。

## ライセンス

本アプリのコードは [MIT License](LICENSE)。翻訳モデル（Argos / Gemma 等）は
それぞれの提供元のライセンスに従います（Gemma 派生は Gemma 利用規約）。

## なぜ Argos が既定なのか

「小さい・低計算コスト・単独動作」という条件では、翻訳専用のNMTモデル（Argos）の
方が、小型の汎用LLMより品質/計算コスト比に優れ、CPUでも即時に動きます。一方で
LLMは文脈やニュアンスに強みがあるため、**より高品質が欲しいとき用に llama.cpp の
Gemma 4 を選べる**ようにしてあります（数GBのメモリと初回DLが必要）。日常は軽い
Argos、必要時だけLLM、という使い分けです。
