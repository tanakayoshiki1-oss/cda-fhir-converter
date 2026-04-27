# 06. CDA→FHIRマッピング定義

## 患者情報（Patient）

| FHIRパス | CDAパス | 変換ルール |
|---------|---------|-----------|
| `Patient.identifier[0].system` | `recordTarget/patientRole/id/@root` | `urn:oid:{root}` |
| `Patient.identifier[0].value` | `recordTarget/patientRole/id/@extension` | そのまま |
| `Patient.name[0].text` | `recordTarget/patientRole/patient/name` | テキストノード結合 |
| `Patient.gender` | `recordTarget/patientRole/patient/administrativeGenderCode/@code` | `M`→`male` / `F`→`female` |
| `Patient.birthDate` | `recordTarget/patientRole/patient/birthTime/@value` | `YYYYMMDD`→`YYYY-MM-DD` |

## 実施機関（Organization）

| FHIRパス | CDAパス | 変換ルール |
|---------|---------|-----------|
| `Organization.identifier[0].system` | `custodian/assignedCustodian/representedCustodianOrganization/id/@root` | `urn:oid:{root}` |
| `Organization.identifier[0].value` | `custodian/assignedCustodian/representedCustodianOrganization/id/@extension` | そのまま |
| `Organization.name` | `custodian/assignedCustodian/representedCustodianOrganization/name` | テキストノード |

## 受診情報（Encounter）

| FHIRパス | CDAパス | 変換ルール |
|---------|---------|-----------|
| `Encounter.status` | - | 固定値: `finished` |
| `Encounter.class.code` | - | 固定値: `AMB` |
| `Encounter.period.start` | `documentationOf/serviceEvent/effectiveTime/low/@value` または `effectiveTime/@value` | `YYYYMMDD`→`YYYY-MM-DD` |
| `Encounter.subject` | - | Patient リソースへの参照 |
| `Encounter.serviceProvider` | - | Organization リソースへの参照 |

## 検査結果（Observation）

各 `entry/observation` 要素から1つの Observation リソースを生成する。

| FHIRパス | CDAパス | 変換ルール |
|---------|---------|-----------|
| `Observation.status` | - | 固定値: `final` |
| `Observation.code.coding[0].system` | `observation/code/@codeSystem` | OIDを正規化 |
| `Observation.code.coding[0].code` | `observation/code/@code` | そのまま |
| `Observation.code.coding[0].display` | `observation/code/@displayName` | そのまま |
| `Observation.effectiveDateTime` | `observation/effectiveTime/@value` | `YYYYMMDD`→`YYYY-MM-DD` |
| `Observation.subject` | - | Patient リソースへの参照 |
| `Observation.encounter` | - | Encounter リソースへの参照 |

### 数値結果（PQ型）

```xml
<value xsi:type="PQ" value="165.3" unit="cm"/>
```

| FHIRパス | CDAパス | 変換ルール |
|---------|---------|-----------|
| `Observation.valueQuantity.value` | `value/@value` | 数値に変換 |
| `Observation.valueQuantity.unit` | `value/@unit` | そのまま |
| `Observation.valueQuantity.system` | - | 固定値: `http://unitsofmeasure.org` |
| `Observation.valueQuantity.code` | `value/@unit` | UCUM単位コードに変換（後述） |

### 定性結果（CD型）

```xml
<value xsi:type="CD" code="−" codeSystem="..." displayName="陰性"/>
```

| FHIRパス | CDAパス | 変換ルール |
|---------|---------|-----------|
| `Observation.valueCodeableConcept.coding[0].code` | `value/@code` | そのまま |
| `Observation.valueCodeableConcept.coding[0].display` | `value/@displayName` | そのまま |

## 単位（CDA→UCUM）変換テーブル

| CDA単位 | UCUM コード |
|---------|------------|
| `cm` | `cm` |
| `kg` | `kg` |
| `kg/m2` | `kg/m2` |
| `mmHg` | `mm[Hg]` |
| `mg/dL` | `mg/dL` |
| `%` | `%` |
| `U/L` | `U/L` |
| `mL/min/1.73m2` | `mL/min/{1.73_m2}` |

## コードシステムマッピング

| CDA codeSystem OID | FHIRシステムURL |
|-------------------|----------------|
| `1.2.392.200119.4.504` | `http://jpfhir.jp/fhir/CodeSystem/JLAC10` |
| `2.16.840.1.113883.6.1` (LOINC) | `http://loinc.org` |

## 未対応項目の扱い

- マッピング定義に存在しない検査コードは変換をスキップし、警告ログに記録
- 必須項目（患者ID、健診日）が欠落している場合はバリデーションエラーとして処理を中断
