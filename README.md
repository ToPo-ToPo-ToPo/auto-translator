# auto-translator

🌐 English version: **[README.en.md](README.en.md)**

DeepL の代わりになる、**単独動作・オフライン**のローカル翻訳アプリです。
ブラウザUIに文章を入力すると即時に翻訳します。外部API・アカウント不要で、
最初のモデルDL後はインターネットも不要です。

- **既定エンジン: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  翻訳専用モデル。CPUのみで動作し、1言語ペアあたり約100〜200MB。
  低計算コストで完全オフライン。
- **任意の小型LLMエンジン: llama.cpp（Gemma 4）** — UIで切替可能。1つのGGUFが
  Apple Silicon（Metal）/ Intel / Linux / Windows で同じように動く高い汎用性。
  既定モデルは Gemma 4 E2B（初回選択時に自動DL）。
- **任意の小型LLMエンジン: MLX（Gemma 4 E2B / E4B）** — Apple Silicon 専用。公式重みから
  自分で変換したローカルMLXモデルを使います（公開はしません）。`tools/build_mlx_model.py`
  で一度だけ作成。
- **GUI:** Python標準ライブラリだけで動くローカルWebページ。入力するそばから
  翻訳します（原文の言語は自動検出）。

## インストールと起動（macOS）

事前に [uv](https://docs.astral.sh/uv/) を入れておきます（未導入なら
`brew install uv`）。

```bash
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
```

あとは clone したフォルダ内の **`auto-translator.app` をダブルクリックするだけ**です。
初回だけアプリが自動で準備し（数秒〜十数秒）、サーバを起動してブラウザを開きます。
2回目以降は即起動します（もう一度クリックしても既存のタブを再表示するだけで、
二重起動しません）。

- **終了:** Dock アイコンを右クリック →「終了」（サーバも停止します）。
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

## 小型LLMエンジン（llama.cpp / 任意）

UIのエンジン欄で **「Gemma 4 E2B (llama.cpp)」** を選ぶと、LLM翻訳に切り替わります。
既定は Argos のままなので、必要なときだけ使えます。

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

## 小型LLMエンジン（MLX / Apple Silicon・任意）

公式重みから**自分で変換したローカルMLXモデル**で動くエンジンです（モデルは公開
しません）。MLX は Apple Silicon で効率的に動きます。**E2B**（軽量）と **E4B**
（高品質・要メモリ増）の2種類を用意できます。

```bash
# 一度だけ実行（作りたい方を選択）
uv run python tools/build_mlx_model.py e2b   # 既定: 約9.5GB DL→約3.3GB（メモリ約4〜5GB）
uv run python tools/build_mlx_model.py e4b   # 高品質: 約16GB DL→約5GB（メモリ約6GB）
uv run python tools/build_mlx_model.py all   # 両方
```

作成後、UIのエンジン欄に **「Gemma 4 E2B (MLX)」** /**「Gemma 4 E4B (MLX)」** が
現れます。未作成のうちは UI 上で「未作成」と理由（実行すべきコマンド）が表示されます。
変換と読み込みは同じ **mlx-vlm 0.6.3** で行う必要があるため、本アプリはこの版に固定。

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
pyproject.toml        依存定義（argostranslate / langdetect / llama-cpp-python / mlx-vlm）。uv 管理
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

## なぜ Argos が既定なのか

「小さい・低計算コスト・単独動作」という条件では、翻訳専用のNMTモデル（Argos）の
方が、小型の汎用LLMより品質/計算コスト比に優れ、CPUでも即時に動きます。一方で
LLMは文脈やニュアンスに強みがあるため、**より高品質が欲しいとき用に llama.cpp の
Gemma 4 を選べる**ようにしてあります（数GBのメモリと初回DLが必要）。日常は軽い
Argos、必要時だけLLM、という使い分けです。
