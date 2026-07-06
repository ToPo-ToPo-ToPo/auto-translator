# インストールと配置

## 前提

- macOS（単体アプリとして使う場合）
- [uv](https://docs.astral.sh/uv/) … `brew install uv` で導入

## 導入

```bash
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
```

clone したフォルダ内の **`auto-translator.app` をダブルクリック**します。初回だけ
アプリが自動で依存環境を準備し（数秒〜十数秒）、**単体ウインドウ**が開きます。
2回目以降は即起動します（起動中に再度クリックしても二重起動しません）。

- **終了:** ウインドウを閉じる（または Dock アイコン右クリック →「終了」）。
- 準備や動作の詳細は `app.log` に記録されます。

## Dock / アプリケーションフォルダに置く

`.app` は**起動役（ランチャー）**で、本体は clone した**プロジェクトフォルダ**
（`app.py` や `.venv` がある場所）です。

- **Dock に入れる:** `auto-translator.app` を Dock にドラッグ。ファイルは移動せず
  参照だけが作られます（コピー不要）。
- **アプリケーションフォルダに入れる:** `.app` を **⌥(option)+ドラッグでコピー**
  して `/Applications` へ（単純ドラッグは「移動」）。コピーでもランチャーが
  プロジェクトフォルダを見つけて起動します。
- ⚠️ **プロジェクトフォルダ本体は残してください。** 削除・移動すると `.app` も
  動かなくなります（`.app` はリモコン、フォルダが本体）。
- **おすすめ:** `.app` をフォルダに置いたまま Dock にドラッグ。
- **`.app` をプロジェクト外（例: `/Applications`）に置く場合:** 環境変数
  `AUTO_TRANSLATE_HOME` に、クローンした auto-translator フォルダの絶対パスを
  設定してください（未設定だと、フォルダ外の `.app` は本体を見つけられません）。

> 起動してもアプリが自動でアプリケーションフォルダへ移動することはありません。

## Windows / Linux（実験的・未検証）

**対応・検証済みは macOS です。** 中核（Argos翻訳）と GUI(pywebview) は
クロスプラットフォームのため Windows / Linux でも動く見込みですが、**ワンクリック
用の `.app` は無く、現状は未検証**です。ターミナルから起動してください
（GUIウインドウを使う場合は `uv sync --extra gui` が必要）。

共通の前提:
- [uv](https://docs.astral.sh/uv/) を導入（Win/Linux のインストール手順は uv 公式参照）
- `git clone` 後、プロジェクトフォルダで実行

```bash
# GUIウインドウを使う場合は gui extra を入れる（無い場合はブラウザ表示になる）:
uv sync --extra gui
uv run python app.py
# 単体ウインドウが出ない/不安定な場合は、確実なブラウザ表示にフォールバック:
AUTO_TRANSLATE_BROWSER=1 uv run python app.py
```

> **依存はコア最小 + 任意 extra です。** extra 無しの `uv sync` では GUI(pywebview)
> も LLM も入りません（Argos 翻訳のヘッドレス利用向け）。GUI は `--extra gui`、
> MLX(Gemma) は `--extra mlx`、両方まとめてなら `--extra app` を付けてください。
> `.app` からのダブルクリック起動は自動で `--extra gui --extra mlx` を入れます。
> 詳細は [development.md](development.md#依存の構成コア--任意-extra) を参照。

### Windows
- ウインドウ表示には **WebView2 ランタイム**が必要です（Windows 10/11 は通常導入済み。
  無い場合は Microsoft から入手）。
- うまく表示されない場合は上記の **ブラウザモード**を使ってください。

### Linux
- pywebview に **GUIバックエンド（GTK または Qt）** が必要です。例:
  ```bash
  uv pip install "pywebview[gtk]"   # もしくは "pywebview[qt]"
  ```
  （GTK系の場合 `gir1.2-webkit2-4.1` などシステムパッケージが別途必要なことがあります）
- 環境構築が難しい場合は **ブラウザモード**（`AUTO_TRANSLATE_BROWSER=1`）が確実です。

### 各OSでのエンジン
- **Argos**: 全OSで動作（既定）。
- **MLX（Gemma 4）**: **Apple Silicon 専用**。Windows/Linux/Intel Mac では導入されず、
  エンジン一覧にも表示されません。
- **llama.cpp**: 任意（`uv sync --extra llamacpp`）。プリビルトwheelがCPUアーキに
  合えば利用可。

> Windows/Linux 向けのワンクリック起動（インストーラ/ランチャー）は今後の課題です。

## ブラウザモード

埋め込みウインドウではなく**実ブラウザ**で開くモードです（日本語入力が確実に
使えます。[トラブルシューティング](troubleshooting.md)参照）。

```bash
AUTO_TRANSLATE_BROWSER=1 uv run python app.py
```

ウインドウを使わずサーバのみで動かす場合は `uv run python app.py --no-window`。
