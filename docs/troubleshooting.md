# トラブルシューティング

困ったときは、まず画面下部の **「ログ」を開いて「コピー」** し、内容を確認/共有して
ください。原因の多くはここに表示されます。

## 日本語入力（IME）が効かない

単体アプリウインドウは埋め込み WebView（macOSは WKWebView）で描画しており、
**日本語などのIME変換が効かない**ことがあります。確実に入力したい場合は
**ブラウザモード**で起動してください（実ブラウザはIMEが確実）:

```bash
AUTO_TRANSLATE_BROWSER=1 uv run python app.py
```

## 初回の翻訳が遅い／止まって見える

- LLM（MLX）を初めて使うときは、モデル（約3.3GB〜）の**ダウンロード**が走ります。
  確認ダイアログでOKした後、**ログパネルに「ダウンロード中 NN% / GB」**が表示されます。
  完了後はオフラインで即時です。
- 軽量・即時がよい場面では、エンジンを **Argos** にすればDL不要で動きます。

## 「ダウンロードしようとする／No safetensors found」

以前のダウンロードが途中で終わると、キャッシュが不完全になります。本アプリは
不足分のみ再取得して補完します。それでも繰り返す場合は、該当キャッシュを削除して
やり直してください:

```bash
rm -rf ~/.cache/huggingface/hub/models--ToPo-ToPo--gemma-4-E2B-it-qat-mlx-4bit
```

## MLX（Gemma）に切替えると「'str' object has no attribute '__module__'」

`transformers 5.13.0` が `mlx-lm` のトークナイザ登録と非互換で、`import mlx_vlm`
時に失敗します（MLXエンジンへ切替えた瞬間に発生）。本アプリは `transformers<5.13`
に制約済みです。古い環境でこのエラーが出る場合は、依存を入れ直してください:

```bash
uv sync
```

それでも `transformers` が 5.13 のままなら、明示的に固定して同期します:

```bash
uv lock && uv sync
uv run python -c "import importlib.metadata as m; print(m.version('transformers'))"  # 5.12.x になればOK
```

## アプリがDockでバウンドするだけで起動しない

初回は依存準備に時間がかかることがあります。少し待っても開かない場合は、ターミナルで
`uv run python app.py` を実行し、表示されるエラーを確認してください（`app.log` にも
記録されます）。

## llama.cpp で「incompatible architecture」エラー

プリビルトwheelがCPUアーキ（例: Apple Silicon に x86_64）と不一致のときに出ます。
macOS では **MLX エンジンの利用を推奨**します。どうしても llama.cpp が必要なら、
ネイティブarch向けに入れ直してください（`uv sync --extra llamacpp` を arm64 環境で）。

## ログの見方・共有

下部「ログ」を開く →「コピー」。起動時のエンジン状態、ダウンロード進捗、翻訳ごとの
リクエスト、エラーのトレースバックが含まれます。不具合報告時に貼ると原因特定が
早くなります。
