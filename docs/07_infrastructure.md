# 07. インフラ構成

## Docker構成

```
docker/
├── Dockerfile          # コンバーターアプリ
└── docker-compose.yml  # アプリ + PostgreSQL
```

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/

CMD ["python", "-m", "src.main"]
```

## docker-compose.yml 概要

```yaml
services:
  converter:
    build: .
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/cda_fhir
      - WATCH_INTERVAL_SECONDS=300
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cda_fhir
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## PostgreSQLスキーマ

```sql
-- 変換ジョブ管理テーブル
CREATE TABLE conversion_jobs (
    id            SERIAL PRIMARY KEY,
    file_name     VARCHAR(255) NOT NULL,
    file_path     TEXT NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    error_type    VARCHAR(100),
    error_message TEXT,
    output_path   TEXT,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON conversion_jobs(status);
CREATE INDEX idx_jobs_file_name ON conversion_jobs(file_name);
```

## 起動手順

```bash
# 初回起動
docker compose up -d

# ログ確認
docker compose logs -f converter

# 停止
docker compose down

# データ含めて完全削除
docker compose down -v
```

## ボリュームマウント

`data/` ディレクトリはホストとコンテナ間でマウント共有するため、  
ホスト側から直接XMLファイルを配置することで変換処理が開始される。

```
ホスト: ./data/input/  ←→  コンテナ: /app/data/input/
```

## ネットワーク

- コンテナ間通信は Docker の内部ネットワーク（`cda-fhir-network`）を使用
- 外部公開ポートは原則なし（将来的なAPI追加時に必要に応じて開放）

## セキュリティ考慮

- DBの認証情報は `.env` ファイルで管理（リポジトリにはコミットしない）
- `.env.example` をリポジトリに含め、必要な変数を明示
- PostgreSQLは外部に公開しない（コンテナ内ネットワークのみ）

## 将来拡張：HAPI FHIRサーバー追加

```yaml
  hapi-fhir:
    image: hapiproject/hapi:latest
    ports:
      - "8080:8080"
    environment:
      - spring.datasource.url=jdbc:postgresql://db:5432/hapi
```

`OUTPUT_MODE=fhir_server` に設定することでPOSTモードに切替可能とする。
