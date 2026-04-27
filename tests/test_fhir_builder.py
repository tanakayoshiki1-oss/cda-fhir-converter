import pytest
from src.converter.fhir_builder import FhirBundleBuilder
from src.converter.cda_parser import CdaData, ObservationData


def make_cda(observations=None):
    return CdaData(
        patient_id="0000123456",
        patient_id_root="1.2.392.100495.20.3.51.11234567",
        patient_name="田中 太郎",
        gender="M",
        birth_date="1965-03-15",
        org_id="1234567890",
        org_id_root="1.2.392.100495.20.3.27",
        org_name="さくら健診クリニック",
        service_date="2024-04-01",
        observations=observations or [],
    )


class TestBundleStructure:
    def test_resource_type_is_bundle(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        assert bundle["resourceType"] == "Bundle"

    def test_bundle_type_is_collection(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        assert bundle["type"] == "collection"

    def test_bundle_has_id(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        assert "id" in bundle

    def test_bundle_has_timestamp(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        assert "timestamp" in bundle

    def test_bundle_has_entries(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        assert len(bundle["entry"]) > 0

    def test_bundle_contains_patient(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Patient" in types

    def test_bundle_contains_organization(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Organization" in types

    def test_bundle_contains_encounter(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Encounter" in types

    def test_bundle_contains_observations(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Observation" in types


class TestPatientResource:
    def setup_method(self):
        self.cda = make_cda()
        bundle = FhirBundleBuilder(self.cda).build()
        self.patient = next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Patient"
        )

    def test_patient_identifier_value(self):
        assert self.patient["identifier"][0]["value"] == "0000123456"

    def test_patient_identifier_system(self):
        assert "1.2.392.100495.20.3.51.11234567" in self.patient["identifier"][0]["system"]

    def test_patient_name(self):
        assert self.patient["name"][0]["text"] == "田中 太郎"

    def test_patient_gender_male(self):
        assert self.patient["gender"] == "male"

    def test_patient_birth_date(self):
        assert self.patient["birthDate"] == "1965-03-15"

    def test_patient_gender_female(self):
        cda = make_cda()
        cda.gender = "F"
        bundle = FhirBundleBuilder(cda).build()
        patient = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        assert patient["gender"] == "female"

    def test_patient_gender_unknown(self):
        cda = make_cda()
        cda.gender = "X"
        bundle = FhirBundleBuilder(cda).build()
        patient = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        assert patient["gender"] == "unknown"


class TestOrganizationResource:
    def setup_method(self):
        bundle = FhirBundleBuilder(make_cda()).build()
        self.org = next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Organization"
        )

    def test_org_name(self):
        assert self.org["name"] == "さくら健診クリニック"

    def test_org_identifier_value(self):
        assert self.org["identifier"][0]["value"] == "1234567890"

    def test_org_identifier_system(self):
        assert "1.2.392.100495.20.3.27" in self.org["identifier"][0]["system"]


class TestEncounterResource:
    def setup_method(self):
        bundle = FhirBundleBuilder(make_cda()).build()
        self.enc = next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Encounter"
        )

    def test_encounter_status(self):
        assert self.enc["status"] == "finished"

    def test_encounter_class_code(self):
        assert self.enc["class"]["code"] == "AMB"

    def test_encounter_period_start(self):
        assert self.enc["period"]["start"] == "2024-04-01"

    def test_encounter_subject_references_patient(self):
        assert self.enc["subject"]["reference"].startswith("Patient/")

    def test_encounter_service_provider_references_org(self):
        assert self.enc["serviceProvider"]["reference"].startswith("Organization/")


class TestObservationResource:
    def _build_pq_observation(self, code="9A751000000000001", display="収縮期血圧",
                               value="135", unit="mmHg"):
        cda = make_cda(observations=[
            ObservationData(
                code=code,
                code_system="1.2.392.200119.4.504",
                display_name=display,
                value_type="PQ",
                value=value,
                unit=unit,
                effective_date="2024-04-01",
            )
        ])
        bundle = FhirBundleBuilder(cda).build()
        return next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Observation"
        )

    def _build_cd_observation(self):
        cda = make_cda(observations=[
            ObservationData(
                code="1A020000000190111",
                code_system="1.2.392.200119.4.504",
                display_name="尿糖",
                value_type="CD",
                value="−",
                effective_date="2024-04-01",
            )
        ])
        bundle = FhirBundleBuilder(cda).build()
        return next(
            e["resource"] for e in bundle["entry"]
            if e["resource"]["resourceType"] == "Observation"
        )

    def test_pq_status_is_final(self):
        obs = self._build_pq_observation()
        assert obs["status"] == "final"

    def test_pq_has_value_quantity(self):
        obs = self._build_pq_observation()
        assert "valueQuantity" in obs

    def test_pq_value(self):
        obs = self._build_pq_observation(value="135")
        assert obs["valueQuantity"]["value"] == 135.0

    def test_pq_unit(self):
        obs = self._build_pq_observation(unit="mmHg")
        assert obs["valueQuantity"]["unit"] == "mmHg"

    def test_pq_ucum_conversion_mmhg(self):
        obs = self._build_pq_observation(unit="mmHg")
        assert obs["valueQuantity"]["code"] == "mm[Hg]"

    def test_pq_ucum_conversion_kg_m2(self):
        obs = self._build_pq_observation(unit="kg/m2")
        assert obs["valueQuantity"]["code"] == "kg/m2"

    def test_pq_ucum_system(self):
        obs = self._build_pq_observation()
        assert obs["valueQuantity"]["system"] == "http://unitsofmeasure.org"

    def test_pq_code(self):
        obs = self._build_pq_observation(code="9A751000000000001")
        assert obs["code"]["coding"][0]["code"] == "9A751000000000001"

    def test_pq_jlac10_system(self):
        obs = self._build_pq_observation()
        assert obs["code"]["coding"][0]["system"] == "http://jpfhir.jp/fhir/CodeSystem/JLAC10"

    def test_pq_subject_references_patient(self):
        obs = self._build_pq_observation()
        assert obs["subject"]["reference"].startswith("Patient/")

    def test_pq_encounter_reference(self):
        obs = self._build_pq_observation()
        assert obs["encounter"]["reference"].startswith("Encounter/")

    def test_pq_effective_date(self):
        obs = self._build_pq_observation()
        assert obs["effectiveDateTime"] == "2024-04-01"

    def test_cd_has_value_codeable_concept(self):
        obs = self._build_cd_observation()
        assert "valueCodeableConcept" in obs

    def test_cd_value_code(self):
        obs = self._build_cd_observation()
        assert obs["valueCodeableConcept"]["coding"][0]["code"] == "−"

    def test_unknown_value_type_excluded(self):
        cda = make_cda(observations=[
            ObservationData(
                code="XXXX",
                code_system="1.2.392.200119.4.504",
                display_name="不明型",
                value_type="UNKNOWN",
                value=None,
            )
        ])
        bundle = FhirBundleBuilder(cda).build()
        obs_list = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation"]
        assert len(obs_list) == 0

    def test_resource_ids_are_unique(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        ids = [e["resource"]["id"] for e in bundle["entry"]]
        assert len(ids) == len(set(ids))

    def test_patient_and_encounter_refs_consistent(self, parsed_cda):
        bundle = FhirBundleBuilder(parsed_cda).build()
        patient = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        encounter = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Encounter")
        obs = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Observation")

        assert obs["subject"]["reference"] == f"Patient/{patient['id']}"
        assert obs["encounter"]["reference"] == f"Encounter/{encounter['id']}"
