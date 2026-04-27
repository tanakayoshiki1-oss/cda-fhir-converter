# 02. 入力仕様

## 対象ファイル

- **形式**: XML（HL7 CDA R2）
- **準拠規格**: 厚生労働省 標準規格3-1b「特定健康診査及び特定保健指導に関するデータ標準仕様書」
- **文字コード**: UTF-8

## フォルダ配置

```
data/input/
└── *.xml   ← 変換対象のCDA XMLファイル
```

- 入力フォルダはシステム起動時に自動作成
- ファイル名に制約なし（拡張子 `.xml` のみ対象）
- サブフォルダは対象外（直下のファイルのみ処理）

## CDAドキュメント構造

特定健診CDAの主要要素：

```xml
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="1.2.392.100495.20.1.31.1"/>  <!-- 特定健診テンプレート -->

  <!-- 文書識別子 -->
  <id root="..." extension="..."/>
  <code code="..." displayName="特定健診"/>
  <effectiveTime value="..."/>  <!-- 健診実施日 -->

  <!-- 患者情報 -->
  <recordTarget>
    <patientRole>
      <id .../>
      <patient>
        <name>...</name>
        <administrativeGenderCode .../>
        <birthTime value="..."/>
      </patient>
    </patientRole>
  </recordTarget>

  <!-- 実施機関 -->
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="..." extension="..."/>
        <name>...</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <!-- 検査結果 -->
  <component>
    <structuredBody>
      <component>
        <section>
          <entry>
            <observation>
              <code code="..." codeSystem="..." displayName="..."/>
              <value xsi:type="PQ" value="..." unit="..."/>
            </observation>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
```

## 主要な検査項目（特定健診標準項目）

| 項目名 | JLAC10コード | 単位 |
|--------|-------------|------|
| 身長 | 9N001000000000001 | cm |
| 体重 | 9N006000000000001 | kg |
| BMI | 9N011000000000001 | kg/m2 |
| 腹囲 | 9N016000000000001 | cm |
| 収縮期血圧 | 9A751000000000001 | mmHg |
| 拡張期血圧 | 9A761000000000001 | mmHg |
| 空腹時血糖 | 3D010000001906269 | mg/dL |
| HbA1c（NGSP） | 3D010000001926201 | % |
| 中性脂肪 | 3F015000002327101 | mg/dL |
| HDLコレステロール | 3F070000002327101 | mg/dL |
| LDLコレステロール | 3F077000002327101 | mg/dL |
| ALT | 3B045000002327101 | U/L |
| AST | 3B035000002327101 | U/L |
| γ-GTP | 3B090000002327101 | U/L |
| 尿糖 | 1A020000000190111 | - |
| 尿蛋白 | 1A030000000190111 | - |
| eGFR / 血清クレアチニン | 3C020000002327101 | mg/dL |

## バリデーション

入力ファイルの事前検証として以下を確認する：

1. XMLとして正しく構文解析できること
2. CDAのルートノード（`ClinicalDocument`）が存在すること
3. 特定健診テンプレートID（`1.2.392.100495.20.1.31.1`）が含まれること
4. 患者ID、健診実施日が存在すること
