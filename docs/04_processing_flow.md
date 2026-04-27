# 04. 処理フロー・フォルダ監視

## フォルダ構成

```
data/
├── input/    # 変換対象XMLを格納する（監視対象）
├── output/   # 変換成功後のFHIR JSONを出力
├── success/  # 変換成功済みXMLを移動
├── error/    # 変換失敗XMLを移動
└── logs/     # エラー詳細ログファイル（.txt）を出力
```

## 監視仕様

- **方式**: 定期ポーリング（APScheduler の `IntervalTrigger`）
- **デフォルト間隔**: 5分（環境変数 `WATCH_INTERVAL_SECONDS` で変更可）
- **対象**: `data/input/` 直下の `*.xml` ファイル
- **サブフォルダ**: 対象外

## 処理フロー

```
[APScheduler]
     │
     ▼（定期実行）
[input/ をスキャン]
     │
     ├── XMLファイルなし → 終了
     │
     └── XMLファイルあり
          │
          ▼（ファイルごとに処理）
     [バリデーション]
          │
          ├── NG → error/へ移動 + エラーログ作成 + DBに失敗記録
          │
          └── OK
               │
               ▼
     [CDAパース]
          │
          ├── エラー → error/へ移動 + エラーログ作成 + DBに失敗記録
          │
          └── 成功
               │
               ▼
     [FHIRリソース生成]
          │
          ├── エラー → error/へ移動 + エラーログ作成 + DBに失敗記録
          │
          └── 成功
               │
               ▼
     [FHIR JSON出力（output/）]
          │
          ▼
     [success/へXMLを移動]
          │
          ▼
     [DBに成功記録]
```

## 並列処理

- 同一実行サイクル内の複数ファイルは**逐次処理**（シングルスレッド）
- 将来的に件数が増えた場合はスレッドプールで並列化を検討

## 二重処理防止

- DBの処理ステータスを参照し、処理中フラグがあるファイルはスキップ
- ファイルロック（`fcntl`）は不使用（Dockerコンテナ単体実行を前提）

## 処理ステータス管理（PostgreSQL）

```sql
CREATE TABLE conversion_jobs (
    id            SERIAL PRIMARY KEY,
    file_name     VARCHAR(255) NOT NULL,
    file_path     TEXT NOT NULL,
    status        VARCHAR(20) NOT NULL,  -- 'pending', 'processing', 'success', 'error'
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    error_message TEXT,
    output_path   TEXT,
    created_at    TIMESTAMP DEFAULT NOW()
);
```

## 環境変数

| 変数名 | デフォルト | 説明 |
|--------|-----------|------|
| `WATCH_INTERVAL_SECONDS` | `300` | 監視間隔（秒） |
| `INPUT_DIR` | `data/input` | 入力フォルダパス |
| `OUTPUT_DIR` | `data/output` | 出力フォルダパス |
| `SUCCESS_DIR` | `data/success` | 成功移動先フォルダ |
| `ERROR_DIR` | `data/error` | 失敗移動先フォルダ |
| `LOG_DIR` | `data/logs` | ログ出力フォルダ |
| `DATABASE_URL` | - | PostgreSQL接続URL |
| `OUTPUT_MODE` | `file` | `file` または `fhir_server`（将来対応） |
| `FHIR_SERVER_URL` | - | HAPI FHIR URL（OUTPUT_MODE=fhir_serverのとき） |
