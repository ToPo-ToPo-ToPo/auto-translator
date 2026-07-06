# エンジンとモデル・設定

UIのエンジン選択で切り替えます。**既定は Argos**（全OS）。MLX / llama.cpp は任意です。

## Argos Translate（既定）

- 翻訳専用のNMTモデル。CPUのみで動作し、**即時・完全オフライン**。
- 1言語ペアあたり約100〜200MB。**初回の言語ペアだけ**自動DL（以降オフライン）。
- 軽量で速いため、日常利用はこれで十分です。

## MLX（Gemma 4）— Apple Silicon 専用・任意

- 導入は任意 extra です（`.app` 起動なら自動、手動なら `uv sync --extra mlx`
  または `pip install "auto-translator[mlx]"`）。
- UIで「**Gemma 4 E2B (MLX)**」「**Gemma 4 E4B (MLX)**」を選択。高品質。
- モデルは公開済みリポジトリを**初回利用時に自動DL**します。
  - E2B: [`ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit`](https://huggingface.co/ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit)（約3.3GB / メモリ約4〜5GB）
  - E4B: [`ToPo-ToPo/gemma-4-E4B-it-qat-mlx-4bit`](https://huggingface.co/ToPo-ToPo/gemma-4-E4B-it-qat-mlx-4bit)（約5GB / メモリ約6GB）
- **未キャッシュ時は確認ダイアログ**（「約N GB をダウンロードします。実行しますか？」）が
  出て、OK後にダウンロードします。進捗はログパネルに表示され、以降はオフライン。
- macOS以外/Intel Mac では mlx-vlm が導入されず、エンジン一覧にも表示されません。
- 自分で変換したローカルモデルを使うこともできます（[development.md](development.md)）。
- 高速化（MTP / speculative decoding）にも対応（[development.md](development.md)）。

## llama.cpp（Gemma 4 GGUF）— 任意・既定では未導入

クロスプラットフォームでLLMを使いたい場合の任意エンジンです（macOSでは MLX 推奨）。
プリビルトwheelがCPUアーキと合わない場合があるため既定では入れません。

```bash
uv sync --extra llamacpp
```

導入後、UIに「Gemma 4 E2B (llama.cpp)」が現れます。既定モデル
（`google/gemma-4-E2B-it-qat-q4_0-gguf`）を初回利用時に自動DLします。

## 設定（環境変数）

| 変数 | 既定値 | 用途 |
|---|---|---|
| `AUTO_TRANSLATE_HOST` | `127.0.0.1` | バインドするホスト |
| `AUTO_TRANSLATE_PORT` | `8765` | ポート |
| `AUTO_TRANSLATE_BROWSER` | _(未設定)_ | `1` で実ブラウザ表示（IME確実） |
| `AUTO_TRANSLATE_NO_WINDOW` | _(未設定)_ | `1` でウインドウを開かずサーバのみ |
| `AUTO_TRANSLATE_MLX_MODEL` | `ToPo-ToPo/gemma-4-E2B-it-qat-mlx-4bit` | MLX(E2B) モデル（ローカルパス or HF repo） |
| `AUTO_TRANSLATE_MLX_E4B_MODEL` | `ToPo-ToPo/gemma-4-E4B-it-qat-mlx-4bit` | MLX(E4B) モデル |
| `AUTO_TRANSLATE_GGUF` | _(未設定)_ | llama.cpp 用ローカルGGUFパス（最優先） |
| `AUTO_TRANSLATE_GGUF_REPO` / `_FILE` | E2B GGUF | llama.cpp で自動DLするHFリポジトリ/ファイル |
| `AUTO_TRANSLATE_IDLE_UNLOAD_SEC` | _(設定パネル)_ | LLM自動解放までの未使用秒数。設定値より優先（`0`で無効） |

### モデルの解決順（MLX）

`AUTO_TRANSLATE_MLX_MODEL`（env）→ ローカル自作モデル（`~/.cache/auto-translator/mlx/`）
→ 公開HFリポジトリ。HFキャッシュに完全に存在する場合はオフラインでロードします
（再ダウンロードしません）。
