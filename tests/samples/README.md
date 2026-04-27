# テストサンプルデータ

## ファイル一覧

| ファイル | 内容 | 期待する結果 |
|---------|------|------------|
| `sample_tokutei_kenshin.xml` | 正常な特定健診CDA（全セクション含む） | 変換成功 → output/にJSON出力 |
| `sample_invalid_no_template.xml` | テンプレートID欠落 | ValidationError → error/に移動 |
| `sample_invalid_broken_xml.xml` | XML構文エラー | XMLSyntaxError → error/に移動 |

## sample_tokutei_kenshin.xml の内容

### 患者情報

| 項目 | 値 |
|------|----|
| 氏名 | 田中 太郎 |
| 性別 | 男性 |
| 生年月日 | 1965年3月15日 |
| 被保険者番号 | 0000123456 |

### 健診実施情報

| 項目 | 値 |
|------|----|
| 実施日 | 2024年4月1日 |
| 実施機関 | さくら健診クリニック（神奈川県川崎市） |
| 保険者 | ○○健康保険組合 |

### 検査結果

| 検査項目 | 値 | 単位 | 参考基準値 |
|---------|-----|------|-----------|
| 身長 | 172.5 | cm | - |
| 体重 | 75.3 | kg | - |
| BMI | 25.3 | kg/m2 | < 25.0 |
| 腹囲 | 88.0 | cm | < 85 (男性) |
| 収縮期血圧 | 135 | mmHg | < 130 |
| 拡張期血圧 | 85 | mmHg | < 85 |
| 空腹時血糖 | 102 | mg/dL | < 100 |
| HbA1c（NGSP） | 5.9 | % | < 5.6 |
| 中性脂肪 | 148 | mg/dL | < 150 |
| HDLコレステロール | 52 | mg/dL | ≥ 40 |
| LDLコレステロール | 138 | mg/dL | < 120 |
| AST | 28 | U/L | ≤ 30 |
| ALT | 35 | U/L | ≤ 30 |
| γ-GTP | 42 | U/L | ≤ 50 |
| 血清クレアチニン | 0.85 | mg/dL | - |
| eGFR | 78.5 | mL/min/1.73m2 | ≥ 60 |
| 尿糖 | 陰性 | - | 陰性 |
| 尿蛋白 | 陰性 | - | 陰性 |

## 手動テスト手順

```bash
# 正常ファイルのテスト
cp tests/samples/sample_tokutei_kenshin.xml data/input/

# エラーファイルのテスト
cp tests/samples/sample_invalid_no_template.xml data/input/

# 変換実行（Docker使用時）
docker compose -f docker/docker-compose.yml up -d

# 結果確認
ls data/output/    # 変換済みJSON
ls data/success/   # 処理済みXML
ls data/error/     # エラーXML
ls data/logs/      # エラーログ
```
