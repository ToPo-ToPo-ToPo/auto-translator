# アンインストール

このアプリが作成したものだけを削除するスクリプトです（無関係なファイルには触れません）。

```bash
./uninstall.sh                # venv・ログ・キャッシュ・Argosモデル・ローカルMLXモデル
./uninstall.sh --keep-models  # ダウンロード/作成済みモデルは残す
./uninstall.sh --yes          # 確認プロンプトを省略
```

- 削除前に**対象とサイズを一覧表示**し、確認を求めます。
- 削除対象: `.venv` / `app.log` / `__pycache__` / Argos のモデル・キャッシュ
  （`~/.local/share/argos-translate` ほか）/ ローカルMLXモデル
  （`~/.cache/auto-translator`）。

仕上げに、Dock から `.app` を外し、プロジェクトフォルダを削除すれば完了です。

## 補足: 共有キャッシュ内のモデル

MLX/llama.cpp が自動DLしたモデルは Hugging Face の共有キャッシュ
（`~/.cache/huggingface`）に保存されます。`uninstall.sh` はここを一括削除しません
（他用途のモデルを誤って消さないため）。不要なら個別に削除してください。例:

```bash
rm -rf ~/.cache/huggingface/hub/models--ToPo-ToPo--gemma-4-E2B-it-qat-mlx-4bit
```
