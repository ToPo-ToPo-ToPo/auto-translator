# auto-translator

🌐 English: **[README.en.md](README.en.md)** ・ 📖 詳しい説明: **[docs/](docs/)**

DeepL の代わりになる、**オフラインで動く単体デスクトップ翻訳アプリ**（macOS）。
ウインドウに入力するとそばから翻訳します。外部API・アカウント不要・ブラウザ不要。

## クイックスタート（macOS）

```bash
brew install uv        # 未導入なら（https://docs.astral.sh/uv/）
git clone https://github.com/ToPo-ToPo-ToPo/auto-translator.git
```

あとは clone したフォルダ内の **`auto-translator.app` をダブルクリック**するだけ。
初回だけ自動で準備し、単体ウインドウが開きます。文章を入力すると即翻訳されます。

## エンジン

- **既定: Argos Translate** — 軽量・即時・完全オフライン。
- **任意: Gemma 4（MLX / Apple Silicon）** — UIで切替。高品質。初回はDL確認あり。

## ドキュメント

- [インストールと配置](docs/installation.md)
- [使い方](docs/usage.md)
- [エンジンとモデル・設定](docs/engines.md)
- [トラブルシューティング](docs/troubleshooting.md)（日本語入力が効かない時など）
- [アンインストール](docs/uninstall.md)
- [開発・自作モデル](docs/development.md)

## ライセンス

[MIT](LICENSE)。翻訳モデル（Argos / Gemma 等）は各提供元のライセンスに従います
（Gemma 派生は [Gemma 利用規約](https://ai.google.dev/gemma/terms)）。
