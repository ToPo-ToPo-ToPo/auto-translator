# auto-translator

🌐 English version: **[README.en.md](README.en.md)**

DeepL の代わりになる、**単独動作・オフライン優先**のローカル翻訳アプリです。
ブラウザUIに文章を入力すると即時に翻訳します。外部API・アカウント不要で、
最初のモデルDL後はインターネットも不要です。

- **既定エンジン: [Argos Translate](https://github.com/argosopentech/argos-translate)** —
  翻訳専用モデル。CPUのみで動作し、1言語ペアあたり約100〜200MB。
  低計算コストで完全オフライン。
- **任意の小型LLMエンジン**（Gemma 4 系）— UIで切替可能:
  - **MLX** — Apple Silicon 向け。既定は Gemma 4 **E2B**（E4B でより高品質）。
  - **llama.cpp** — 任意の小型 Gemma 4 GGUF。
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
- **小型LLM（MLX / Gemma 4 E2B）:** Apple Silicon の Mac では**自動で導入**され、
  UIのエンジン欄に出ます（モデル本体はそのエンジンを初めて選んだ時にDL）。

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

## 小型LLMバックエンド

**MLX（Gemma 4）は Apple Silicon の macOS では自動でインストール**されます。
UIのエンジン欄で選ぶだけで使えます（モデルの重みは初回選択時にDL）。それ以外の
プラットフォームではスキップされます。別のMLXモデルを使いたい場合:

```bash
# E4B（高品質）に上げる / 4bit ビルド（省メモリ）に下げる
export AUTO_TRANSLATE_MLX_MODEL=Rapid42/gemma-4-E4B-it-MLX
# export AUTO_TRANSLATE_MLX_MODEL=unsloth/gemma-4-E2B-it-UD-MLX-4bit
```

llama.cpp エンジンは任意導入です（GGUFファイルが必要）:

```bash
uv sync --extra llamacpp
export AUTO_TRANSLATE_GGUF=/path/to/gemma-4-E2B-it.gguf
```

アプリを再起動すると、エンジン欄に新しいバックエンドが現れます。

## 設定（環境変数）

| 変数 | 既定値 | 用途 |
|---|---|---|
| `AUTO_TRANSLATE_HOST` | `127.0.0.1` | バインドするホスト |
| `AUTO_TRANSLATE_PORT` | `8765` | ポート |
| `AUTO_TRANSLATE_MLX_MODEL` | `Rapid42/gemma-4-E2B-it-MLX` | MLXモデルID（Gemma 4 E2B/E4B） |
| `AUTO_TRANSLATE_GGUF` | _(未設定)_ | llama.cpp エンジン用 GGUF のパス |

## 構成

```
auto-translator.app   ダブルクリック起動の macOS ランチャー（uv sync + uv run app.py）
pyproject.toml        依存定義（Apple Silicon は MLX 自動 / llamacpp は extra）。uv 管理
app.py                標準ライブラリの HTTPサーバ: /api/config, /api/translate, web/ 配信
web/index.html        UI（素のJS、入力に連動した自動翻訳）
engines/              プラガブルなバックエンド（argos / mlx / llamacpp）。遅延import
languages.py          言語リストとコード正規化
```

エンジン追加 = `engines/` に `NAME` / `LABEL` / `is_available()` /
`translate(text, src, tgt, on_status=None)` を持つモジュールを置き、
`engines/__init__.py` に登録するだけ。

## アンインストール

このアプリが作成したものだけを削除するスクリプトです（無関係なファイルには触れません）:

```bash
./uninstall.sh                # venv・ログ・キャッシュ・Argos言語モデル
./uninstall.sh --keep-models  # Argosモデルは残す
./uninstall.sh --all          # 本アプリの Gemma 4 LLM のDL分も削除
./uninstall.sh --yes          # 確認プロンプトを省略
```

削除前に対象とサイズを一覧表示し、確認を求めます。`--all` は**このアプリが
DLする特定の Gemma 4 リポジトリ**（`Rapid42/gemma-4-E2B-it-MLX` と文書化された
代替）**のみ**を削除し、共有 Hugging Face キャッシュ内のあなたの他モデルには
触れません。最後に、Dock から `.app` を外し、プロジェクトフォルダを削除すれば完了です。

## なぜ既定が汎用LLMではなく Argos なのか

「小さい・低計算コスト・単独動作」という条件では、翻訳専用のNMTモデルの方が、
小さな汎用LLMより品質/計算コスト比に優れ、CPUでも快適に動きます。LLMエンジンは
柔軟性が欲しいときのために用意してありますが、既定はコストを低く保ちます。
