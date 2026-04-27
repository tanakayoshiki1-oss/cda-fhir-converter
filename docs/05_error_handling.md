# 05. エラー処理

## エラー分類

| エラー種別 | 説明 | 対応 |
|-----------|------|------|
| バリデーションエラー | XMLが不正・テンプレートID不一致 | error/移動 + ログ |
| パースエラー | XML解析失敗 | error/移動 + ログ |
| マッピングエラー | CDA→FHIR変換失敗 | error/移動 + ログ |
| 出力エラー | JSONファイル書き込み失敗 | error/移動 + ログ |
| DBエラー | PostgreSQL接続・書き込み失敗 | アプリログに記録・処理継続 |

## ファイル移動ルール

### 成功時

```
data/input/20240401_12345678.xml
  → data/success/20240401_12345678.xml
data/output/20240401_12345678_20240401T123456.json  ← FHIR JSON
```

### 失敗時

```
data/input/20240401_12345678.xml
  → data/error/20240401_12345678.xml
data/logs/20240401_12345678_20240401T123456_error.txt  ← エラーログ
```

## エラーログフォーマット

`data/logs/{ファイル名}_{タイムスタンプ}_error.txt`

```
=== CDA FHIR Converter - Error Report ===
File       : 20240401_12345678.xml
Timestamp  : 2024-04-01T12:34:56
Error Type : ValidationError
Message    : テンプレートID '1.2.392.100495.20.1.31.1' が見つかりません

Stack Trace:
Traceback (most recent call last):
  File "/app/src/converter/cda_parser.py", line 45, in validate
    raise ValidationError(...)
ValidationError: テンプレートID '1.2.392.100495.20.1.31.1' が見つかりません

CDA Snippet (抜粋):
<ClinicalDocument xmlns="urn:hl7-org:v3">
  ...
</ClinicalDocument>
```

## 同名ファイルの衝突処理

- `error/` および `success/` に同名ファイルが既にある場合は、タイムスタンプサフィックスを付与して保存
- 例: `20240401_12345678_1.xml`、`20240401_12345678_2.xml`

## リトライ

- 自動リトライは行わない
- `error/` フォルダのファイルを `input/` に手動で戻すことで再処理可能
- （将来対応）管理APIによる再処理トリガー

## DBエラー時の動作

- PostgreSQLへの接続失敗・書き込み失敗はアプリケーションログ（標準出力）に記録
- DBエラーは変換処理を中断しない（ファイル変換自体は完了させる）
- DBが復旧した際に未記録ジョブを自動的にリカバリする仕組みは将来対応

## アプリケーションログ

Pythonの標準 `logging` モジュールを使用し、標準出力に出力：

```
2024-04-01 12:34:56 [INFO]  Watcher started. Interval: 300s
2024-04-01 12:34:56 [INFO]  Scanning: data/input/
2024-04-01 12:34:57 [INFO]  Processing: 20240401_12345678.xml
2024-04-01 12:34:57 [INFO]  Conversion success: 20240401_12345678.xml → output/20240401_12345678_20240401T123456.json
2024-04-01 12:35:00 [ERROR] Conversion failed: bad_file.xml - ValidationError: ...
```

Dockerコンテナとして動作するため、`docker logs` コマンドで確認可能。
