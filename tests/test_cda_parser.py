import pytest
from pathlib import Path
from src.converter.cda_parser import CdaParser, ValidationError


class TestValidate:
    def test_valid_xml_passes(self, valid_xml_path):
        parser = CdaParser(valid_xml_path)
        parser.validate()  # 例外が発生しないこと

    def test_missing_template_raises(self, no_template_xml_path):
        parser = CdaParser(no_template_xml_path)
        with pytest.raises(ValidationError, match="テンプレートID"):
            parser.validate()

    def test_broken_xml_raises(self, broken_xml_path):
        parser = CdaParser(broken_xml_path)
        with pytest.raises(ValidationError, match="XML構文エラー"):
            parser.validate()

    def test_missing_patient_id_raises(self, tmp_path):
        xml = tmp_path / "no_patient_id.xml"
        xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="1.2.392.100495.20.1.31.1"/>
  <id root="1.2.392.100495.20.3.27.1234" extension="202404010001"/>
  <effectiveTime value="20240401"/>
  <recordTarget>
    <patientRole>
      <!-- id 要素が欠落 -->
      <patient>
        <name use="L"><family>テスト</family></name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19650315"/>
      </patient>
    </patientRole>
  </recordTarget>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="1.2.392.100495.20.3.27" extension="1234567890"/>
        <name>テスト機関</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <component><structuredBody/></component>
</ClinicalDocument>""",
            encoding="utf-8",
        )
        parser = CdaParser(xml)
        with pytest.raises(ValidationError, match="患者ID"):
            parser.validate()

    def test_file_not_found_raises(self, tmp_path):
        parser = CdaParser(tmp_path / "nonexistent.xml")
        with pytest.raises(ValidationError):
            parser.validate()


class TestParse:
    def test_patient_id(self, parsed_cda):
        assert parsed_cda.patient_id == "0000123456"

    def test_patient_id_root(self, parsed_cda):
        assert parsed_cda.patient_id_root == "1.2.392.100495.20.3.51.11234567"

    def test_patient_name(self, parsed_cda):
        assert "田中" in parsed_cda.patient_name
        assert "太郎" in parsed_cda.patient_name

    def test_patient_gender_male(self, parsed_cda):
        assert parsed_cda.gender == "M"

    def test_patient_birth_date(self, parsed_cda):
        assert parsed_cda.birth_date == "1965-03-15"

    def test_org_name(self, parsed_cda):
        assert parsed_cda.org_name == "さくら健診クリニック"

    def test_org_id(self, parsed_cda):
        assert parsed_cda.org_id == "1234567890"

    def test_service_date(self, parsed_cda):
        assert parsed_cda.service_date == "2024-04-01"

    def test_observations_not_empty(self, parsed_cda):
        assert len(parsed_cda.observations) > 0

    def test_pq_observation_present(self, parsed_cda):
        pq_obs = [o for o in parsed_cda.observations if o.value_type == "PQ"]
        assert len(pq_obs) > 0

    def test_cd_observation_present(self, parsed_cda):
        cd_obs = [o for o in parsed_cda.observations if o.value_type == "CD"]
        assert len(cd_obs) > 0

    def test_height_observation(self, parsed_cda):
        height = next(
            (o for o in parsed_cda.observations if o.display_name == "身長"), None
        )
        assert height is not None
        assert height.value == "172.5"
        assert height.unit == "cm"

    def test_sbp_observation(self, parsed_cda):
        sbp = next(
            (o for o in parsed_cda.observations if o.display_name == "収縮期血圧"), None
        )
        assert sbp is not None
        assert sbp.value == "135"
        assert sbp.unit == "mmHg"

    def test_urine_glucose_observation(self, parsed_cda):
        urine = next(
            (o for o in parsed_cda.observations if o.display_name == "尿糖"), None
        )
        assert urine is not None
        assert urine.value_type == "CD"
        assert urine.value == "−"

    def test_date_normalization(self, tmp_path):
        """生年月日・健診日のYYYYMMDD→YYYY-MM-DD変換を確認"""
        xml = tmp_path / "test.xml"
        xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="1.2.392.100495.20.1.31.1"/>
  <id root="1.2.392.100495.20.3.27.1234" extension="202404010001"/>
  <effectiveTime value="20231015"/>
  <recordTarget>
    <patientRole>
      <id root="1.2.392.100495.20.3.51.11234567" extension="1111111111"/>
      <patient>
        <name use="L"><family>日付</family><given>テスト</given></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19900630"/>
      </patient>
    </patientRole>
  </recordTarget>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="1.2.392.100495.20.3.27" extension="1234567890"/>
        <name>テスト機関</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <component><structuredBody/></component>
</ClinicalDocument>""",
            encoding="utf-8",
        )
        parser = CdaParser(xml)
        parser.validate()
        data = parser.parse()
        assert data.birth_date == "1990-06-30"
        assert data.service_date == "2023-10-15"

    def test_gender_female(self, tmp_path):
        xml = tmp_path / "female.xml"
        xml.write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="1.2.392.100495.20.1.31.1"/>
  <id root="1.2.392.100495.20.3.27.1234" extension="202404010001"/>
  <effectiveTime value="20240401"/>
  <recordTarget>
    <patientRole>
      <id root="1.2.392.100495.20.3.51.11234567" extension="2222222222"/>
      <patient>
        <name use="L"><family>女性</family><given>テスト</given></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19750520"/>
      </patient>
    </patientRole>
  </recordTarget>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="1.2.392.100495.20.3.27" extension="1234567890"/>
        <name>テスト機関</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <component><structuredBody/></component>
</ClinicalDocument>""",
            encoding="utf-8",
        )
        parser = CdaParser(xml)
        parser.validate()
        data = parser.parse()
        assert data.gender == "F"
