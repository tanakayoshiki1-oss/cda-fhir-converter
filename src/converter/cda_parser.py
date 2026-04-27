from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from lxml import etree

NS = {"hl7": "urn:hl7-org:v3", "xsi": "http://www.w3.org/2001/XMLSchema-instance"}
TOKUTEI_KENSHIN_TEMPLATE = "1.2.392.100495.20.1.31.1"


class ValidationError(Exception):
    pass


@dataclass
class ObservationData:
    code: str
    code_system: str
    display_name: str
    value_type: str  # 'PQ' or 'CD'
    value: Optional[str] = None
    unit: Optional[str] = None
    effective_date: Optional[str] = None


@dataclass
class CdaData:
    patient_id: str
    patient_id_root: str
    patient_name: str
    gender: str
    birth_date: str
    org_id: str
    org_id_root: str
    org_name: str
    service_date: str
    observations: list[ObservationData] = field(default_factory=list)


class CdaParser:
    def __init__(self, xml_path: Path):
        self.xml_path = xml_path
        self.tree = None
        self.root = None

    def validate(self):
        try:
            self.tree = etree.parse(str(self.xml_path))
            self.root = self.tree.getroot()
        except etree.XMLSyntaxError as e:
            raise ValidationError(f"XML構文エラー: {e}")
        except OSError as e:
            raise ValidationError(f"ファイル読み込みエラー: {e}")

        if self.root.tag != f"{{{NS['hl7']}}}ClinicalDocument":
            raise ValidationError("ルートノードが ClinicalDocument ではありません")

        templates = self.root.findall("hl7:templateId", NS)
        roots = [t.get("root", "") for t in templates]
        if TOKUTEI_KENSHIN_TEMPLATE not in roots:
            raise ValidationError(f"テンプレートID '{TOKUTEI_KENSHIN_TEMPLATE}' が見つかりません")

        if not self._find_text("hl7:recordTarget/hl7:patientRole/hl7:id/@extension"):
            raise ValidationError("患者IDが見つかりません")

    def parse(self) -> CdaData:
        patient_role = self.root.find("hl7:recordTarget/hl7:patientRole", NS)
        patient = patient_role.find("hl7:patient", NS)
        org = self.root.find(
            "hl7:custodian/hl7:assignedCustodian/hl7:representedCustodianOrganization", NS
        )

        service_date = self._extract_service_date()

        return CdaData(
            patient_id=patient_role.find("hl7:id", NS).get("extension", ""),
            patient_id_root=patient_role.find("hl7:id", NS).get("root", ""),
            patient_name=self._extract_name(patient),
            gender=patient.find("hl7:administrativeGenderCode", NS).get("code", ""),
            birth_date=self._normalize_date(
                patient.find("hl7:birthTime", NS).get("value", "")
            ),
            org_id=org.find("hl7:id", NS).get("extension", ""),
            org_id_root=org.find("hl7:id", NS).get("root", ""),
            org_name=org.findtext("hl7:name", default="", namespaces=NS),
            service_date=service_date,
            observations=self._extract_observations(),
        )

    def _extract_service_date(self) -> str:
        low = self.root.find(
            "hl7:documentationOf/hl7:serviceEvent/hl7:effectiveTime/hl7:low", NS
        )
        if low is not None:
            return self._normalize_date(low.get("value", ""))
        eff = self.root.find("hl7:effectiveTime", NS)
        if eff is not None:
            return self._normalize_date(eff.get("value", ""))
        return ""

    def _extract_observations(self) -> list[ObservationData]:
        observations = []
        for obs in self.root.iter(f"{{{NS['hl7']}}}observation"):
            code_el = obs.find("hl7:code", NS)
            value_el = obs.find("hl7:value", NS)
            eff_el = obs.find("hl7:effectiveTime", NS)
            if code_el is None or value_el is None:
                continue

            xsi_type = value_el.get(f"{{{NS['xsi']}}}type", "")
            value_type = xsi_type.split(":")[-1] if ":" in xsi_type else xsi_type

            obs_data = ObservationData(
                code=code_el.get("code", ""),
                code_system=code_el.get("codeSystem", ""),
                display_name=code_el.get("displayName", ""),
                value_type=value_type,
                effective_date=self._normalize_date(eff_el.get("value", "")) if eff_el is not None else None,
            )

            if value_type == "PQ":
                obs_data.value = value_el.get("value")
                obs_data.unit = value_el.get("unit")
            elif value_type == "CD":
                obs_data.value = value_el.get("code")

            observations.append(obs_data)
        return observations

    def _extract_name(self, patient_el) -> str:
        name_el = patient_el.find("hl7:name", NS)
        if name_el is None:
            return ""
        parts = [t.strip() for t in name_el.itertext() if t.strip()]
        return " ".join(parts)

    def _normalize_date(self, value: str) -> str:
        if len(value) >= 8:
            return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
        return value

    def _find_text(self, xpath: str) -> Optional[str]:
        results = self.root.xpath(xpath, namespaces=NS)
        return results[0] if results else None
