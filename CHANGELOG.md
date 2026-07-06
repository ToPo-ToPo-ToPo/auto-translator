# 変更履歴（Changelog）

このプロジェクトの主な変更点をまとめます。書式は
[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠し、
バージョンは [セマンティック バージョニング](https://semver.org/lang/ja/) に従います。

## [1.2.0] - 未リリース

### 追加
- **言い換え候補 → 文全体の自動調整（DeepL風）:** 訳文の単語をクリック
  （またはフレーズをドラッグ選択）すると言い換え候補を表示し、選ぶとその語を
  置き換えたうえで、選択に合わせて**文全体を自然に再調整**します。LLMエンジン
  （MLX / llama.cpp）選択時のみ。単語境界の判定に `Intl.Segmenter` を用い、
  日本語など空白のない言語にも対応。
- API エンドポイント `POST /api/rephrase`（候補選択後の文再調整）と
  `GET /api/version`（ソースの指紋）を追加。

### 変更
- **ソース変更の反映を「起動時チェック」方式に:** アプリ稼働中はソースを監視
  せず、`.app` を Dock から起動したときに、稼働中サーバのコードがディスク上の
  内容と一致するか確認し、古ければ停止して新しいコードで起動し直します。
  `web/` の変更はページが `/api/version` をポーリングして自動リロード。
  再起動・リロード時も入力テキスト等を復元（10分以内）。
- 依存構成の記述を整理（GUI(pywebview)・MLX(Apple Silicon) はコア、`llama.cpp`
  のみ任意 extra）。ドキュメント（usage / development / installation / engines）を更新。

### 修正
- 言い換え候補で、モデルが単語ではなく文全体を返した場合に、原文との差分から
  変更部分だけを抽出して候補に整えるよう修正。

## [1.1.0] - 2026-07-04

### 追加
- 設定パネル（⚙）: テーマ、文字サイズ、自動翻訳の待ち時間、LLM パラメータ
  （temperature / 最大トークン）、未使用モデルの自動解放時間などを設定可能に。
- 未使用 LLM モデルの自動解放（アイドル時にメモリを解放し、次回翻訳で再ロード）。
- 訳文の後編集: 翻訳結果をその場で編集・範囲選択でき、単語の言い換え候補を表示。

### 変更
- 依存パッケージの更新。

### 修正
- 言語の自動検出の精度と挙動を改善。
- transformers 5.13.0 で MLX（Gemma）エンジンが `import mlx_vlm` 時に
  クラッシュする問題を修正（transformers を 5.13 未満に制約）。

## [1.0.0] - 2026-06-28

### 追加
- 初回公開リリース。オフライン前提のローカル翻訳デスクトップアプリ。
- 既定エンジンに Argos Translate（NMT）を採用（全OS・軽量・即時・完全オフライン）。
- MLX（Gemma 4 E2B / E4B）エンジン（Apple Silicon 専用）。
- llama.cpp（Gemma 4 GGUF）エンジン（任意 extra）。
- 単体デスクトップウインドウ（pywebview / macOS は WKWebView）と、実ブラウザで
  開くブラウザモード（`AUTO_TRANSLATE_BROWSER=1`）。
- 折りたたみ可能・コピー可能なログパネル、言語自動検出、エンジン別の利用可否表示。

[1.2.0]: https://github.com/ToPo-ToPo-ToPo/auto-translator/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/ToPo-ToPo-ToPo/auto-translator/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/ToPo-ToPo-ToPo/auto-translator/releases/tag/v1.0.0
