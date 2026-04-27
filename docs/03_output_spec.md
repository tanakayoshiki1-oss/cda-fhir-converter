# 03. 出力仕様

## 出力フォーマット

- **形式**: HL7 FHIR R4 JSON
- **構造**: Bundle（type: `collection`）
- **文字コード**: UTF-8
- **ファイル名**: `{入力ファイル名（拡張子なし）}_{タイムスタンプ}.json`

例: `20240401_12345678.xml` → `20240401_12345678_20240401T123456.json`

## 出力フォルダ

```
data/output/
└── *.json  ← 変換済みFHIR Bundle JSON
```

## 生成するFHIRリソース

### Bundle（エントリーポイント）

```json
{
  "resourceType": "Bundle",
  "id": "<UUID>",
  "type": "collection",
  "timestamp": "<変換実行日時>",
  "entry": [
    { "resource": { ... } },
    ...
  ]
}
```

### 含まれるリソース一覧

| リソース | 説明 | CDAの対応要素 |
|---------|------|--------------|
| `Patient` | 患者情報 | `recordTarget/patientRole` |
| `Organization` | 健診実施機関 | `custodian` |
| `Practitioner` | 担当医師 | `legalAuthenticator` |
| `Encounter` | 健診実施情報 | `documentationOf/serviceEvent` |
| `Observation` | 各検査結果 | `entry/observation`（複数） |

### Patient リソース

```json
{
  "resourceType": "Patient",
  "id": "<UUID>",
  "identifier": [
    {
      "system": "urn:oid:<CDA id root>",
      "value": "<CDA id extension>"
    }
  ],
  "name": [
    {
      "use": "official",
      "text": "<患者氏名>"
    }
  ],
  "gender": "male" | "female" | "unknown",
  "birthDate": "YYYY-MM-DD"
}
```

### Encounter リソース

```json
{
  "resourceType": "Encounter",
  "id": "<UUID>",
  "status": "finished",
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB"
  },
  "type": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "310058008",
          "display": "特定健康診査"
        }
      ]
    }
  ],
  "subject": { "reference": "Patient/<UUID>" },
  "serviceProvider": { "reference": "Organization/<UUID>" },
  "period": {
    "start": "YYYY-MM-DD"
  }
}
```

### Observation リソース（検査結果）

```json
{
  "resourceType": "Observation",
  "id": "<UUID>",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "exam"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://jpfhir.jp/fhir/CodeSystem/JLAC10",
        "code": "<JLAC10コード>",
        "display": "<項目名>"
      }
    ]
  },
  "subject": { "reference": "Patient/<UUID>" },
  "encounter": { "reference": "Encounter/<UUID>" },
  "effectiveDateTime": "YYYY-MM-DD",
  "valueQuantity": {
    "value": <数値>,
    "unit": "<単位>",
    "system": "http://unitsofmeasure.org",
    "code": "<UCUM単位>"
  }
}
```

### 定性的な検査結果（尿糖・尿蛋白等）

```json
{
  "valueCodeableConcept": {
    "coding": [
      {
        "system": "http://jpfhir.jp/fhir/CodeSystem/observation-result-urine",
        "code": "-" | "+-" | "+" | "2+" | "3+",
        "display": "陰性" | "疑陽性" | "陽性" | "2+" | "3+"
      }
    ]
  }
}
```

## UUIDの生成方針

- 全リソースのIDはUUID v4（ランダム）を使用
- 同一変換処理内でリソース間の参照は生成したUUIDで解決

## 将来対応：HAPI FHIRへのPOST

- `type: transaction` のBundleに変更
- 各エントリーに `request` ブロック追加（`PUT /Patient/<id>`等）
- 環境変数でモード切替（`OUTPUT_MODE=file` / `fhir_server`）
