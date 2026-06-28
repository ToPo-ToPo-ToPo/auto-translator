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
- **フォルダごと引っ越す場合:** 移動後、ランチャー
  （`auto-translator.app/Contents/MacOS/launch`）内のフォールバック用パスを新しい
  場所に書き換えると、`/Applications` のコピーも追従します。

> 起動してもアプリが自動でアプリケーションフォルダへ移動することはありません。

## macOS 以外 / ターミナルから起動

```bash
cd auto-translator
uv run python app.py
```

pywebview の各OSバックエンドで単体ウインドウが開きます。ウインドウを使わず
サーバのみで動かす場合は `uv run python app.py --no-window`。

## ブラウザモード

埋め込みウインドウではなく**実ブラウザ**で開くモードです（日本語入力が確実に
使えます。[トラブルシューティング](troubleshooting.md)参照）。

```bash
AUTO_TRANSLATE_BROWSER=1 uv run python app.py
```
