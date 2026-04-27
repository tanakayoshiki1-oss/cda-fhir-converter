# cda-fhir-converter

特定健診XML（HL7 CDA形式、厚生労働省標準規格3-1b準拠）をHL7 FHIR R4形式に変換するシステムです。

## 概要

特定のフォルダを定期監視し、格納されたXMLファイルを自動的にFHIR形式へ変換します。
変換結果はJSONファイルとして出力し、将来的にはHAPI FHIRサーバーへのPOSTにも対応予定です。

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [01_overview.md](docs/01_overview.md) | プロジェクト概要・目的 |
| [02_input_spec.md](docs/02_input_spec.md) | 入力仕様（特定健診XML） |
| [03_output_spec.md](docs/03_output_spec.md) | 出力仕様（FHIRリソース） |
| [04_processing_flow.md](docs/04_processing_flow.md) | 処理フロー・フォルダ監視 |
| [05_error_handling.md](docs/05_error_handling.md) | エラー処理 |
| [06_fhir_mapping.md](docs/06_fhir_mapping.md) | CDA→FHIRマッピング定義 |
| [07_infrastructure.md](docs/07_infrastructure.md) | Docker・PostgreSQL構成 |

## 技術スタック

- **言語**: Python 3.11+
- **XMLパース**: lxml
- **FHIRモデル**: fhir.resources
- **スケジューラ**: APScheduler
- **データベース**: PostgreSQL（変換ログ・ステータス管理）
- **インフラ**: Docker / Docker Compose

## フォルダ構成

```
data/
├── input/      # 変換対象XMLを格納
├── output/     # 変換成功後のFHIR JSONを出力
├── success/    # 変換成功済みXMLを移動
├── error/      # 変換失敗XMLを移動
└── logs/       # エラー詳細ログ
```

## クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/tanakayoshiki1-oss/cda-fhir-converter.git
cd cda-fhir-converter

# Docker Composeで起動
docker compose up -d

# 変換対象XMLをinputフォルダに配置
cp your_file.xml data/input/
```

## ライセンス

MIT
