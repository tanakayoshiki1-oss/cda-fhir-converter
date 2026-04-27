import uuid
from datetime import datetime, timezone
from src.converter.cda_parser import CdaData, ObservationData

JLAC10_SYSTEM = "http://jpfhir.jp/fhir/CodeSystem/JLAC10"
UCUM_SYSTEM = "http://unitsofmeasure.org"

UNIT_TO_UCUM = {
    "cm": "cm",
    "kg": "kg",
    "kg/m2": "kg/m2",
    "mmHg": "mm[Hg]",
    "mg/dL": "mg/dL",
    "%": "%",
    "U/L": "U/L",
    "mL/min/1.73m2": "mL/min/{1.73_m2}",
}

GENDER_MAP = {
    "M": "male",
    "F": "female",
}

OID_TO_FHIR_SYSTEM = {
    "1.2.392.200119.4.504": JLAC10_SYSTEM,
    "2.16.840.1.113883.6.1": "http://loinc.org",
}


class FhirBundleBuilder:
    def __init__(self, cda_data: CdaData):
        self.data = cda_data
        self.patient_id = str(uuid.uuid4())
        self.org_id = str(uuid.uuid4())
        self.encounter_id = str(uuid.uuid4())

    def build(self) -> dict:
        entries = [
            {"resource": self._build_patient()},
            {"resource": self._build_organization()},
            {"resource": self._build_encounter()},
        ]
        for obs in self.data.observations:
            resource = self._build_observation(obs)
            if resource:
                entries.append({"resource": resource})

        return {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": entries,
        }

    def _build_patient(self) -> dict:
        return {
            "resourceType": "Patient",
            "id": self.patient_id,
            "identifier": [
                {
                    "system": f"urn:oid:{self.data.patient_id_root}",
                    "value": self.data.patient_id,
                }
            ],
            "name": [{"use": "official", "text": self.data.patient_name}],
            "gender": GENDER_MAP.get(self.data.gender, "unknown"),
            "birthDate": self.data.birth_date,
        }

    def _build_organization(self) -> dict:
        return {
            "resourceType": "Organization",
            "id": self.org_id,
            "identifier": [
                {
                    "system": f"urn:oid:{self.data.org_id_root}",
                    "value": self.data.org_id,
                }
            ],
            "name": self.data.org_name,
        }

    def _build_encounter(self) -> dict:
        return {
            "resourceType": "Encounter",
            "id": self.encounter_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
            },
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "310058008",
                            "display": "特定健康診査",
                        }
                    ]
                }
            ],
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "serviceProvider": {"reference": f"Organization/{self.org_id}"},
            "period": {"start": self.data.service_date},
        }

    def _build_observation(self, obs: ObservationData) -> dict | None:
        fhir_system = OID_TO_FHIR_SYSTEM.get(obs.code_system, f"urn:oid:{obs.code_system}")

        resource = {
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "exam",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": fhir_system,
                        "code": obs.code,
                        "display": obs.display_name,
                    }
                ]
            },
            "subject": {"reference": f"Patient/{self.patient_id}"},
            "encounter": {"reference": f"Encounter/{self.encounter_id}"},
            "effectiveDateTime": obs.effective_date or self.data.service_date,
        }

        if obs.value_type == "PQ" and obs.value is not None:
            resource["valueQuantity"] = {
                "value": float(obs.value),
                "unit": obs.unit,
                "system": UCUM_SYSTEM,
                "code": UNIT_TO_UCUM.get(obs.unit or "", obs.unit or ""),
            }
        elif obs.value_type == "CD" and obs.value is not None:
            resource["valueCodeableConcept"] = {
                "coding": [{"code": obs.value, "display": obs.display_name}]
            }
        else:
            return None

        return resource
