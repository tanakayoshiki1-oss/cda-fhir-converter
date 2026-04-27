"""
結合テスト: XML→FHIR変換 + PostgreSQL書き込みの一連の流れを検証
- testcontainers により実際のPostgreSQLコンテナを使用
- Dockerが起動している必要があります
"""
import json
import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

from src.db.models import ConversionJob
from tests.integration.conftest import requires_docker

SAMPLES_DIR = Path(__file__).parent.parent / "samples"


def run_pipeline_with_db(xml_path: Path, data_dirs: dict, db_session):
    env = {
        "OUTPUT_DIR": str(data_dirs["output"]),
        "SUCCESS_DIR": str(data_dirs["success"]),
        "ERROR_DIR": str(data_dirs["error"]),
        "LOG_DIR": str(data_dirs["logs"]),
    }
    with patch.dict(os.environ, env):
        import importlib
        import src.converter.pipeline as pipeline_mod
        importlib.reload(pipeline_mod)
        pipeline_mod.convert_file(xml_path, db_session=db_session)


@pytest.fixture
def data_dirs(tmp_path):
    dirs = {
        "input": tmp_path / "input",
        "output": tmp_path / "output",
        "success": tmp_path / "success",
        "error": tmp_path / "error",
        "logs": tmp_path / "logs",
    }
    for d in dirs.values():
        d.mkdir()
    return dirs


# ==============================================================
# DB書き込み: 成功ケース
# ==============================================================

@requires_docker
class TestSuccessJobRecording:
    def test_job_created_with_processing_status(self, data_dirs, db_session):
        """変換開始時にDBジョブが作成されること"""
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        jobs = db_session.query(ConversionJob).all()
        assert len(jobs) == 1

    def test_job_status_is_success(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.status == "success"

    def test_job_file_name_recorded(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.file_name == "sample.xml"

    def test_job_output_path_recorded(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.output_path is not None
        assert job.output_path.endswith(".json")

    def test_job_completed_at_set(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.completed_at is not None

    def test_job_started_at_set(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.started_at is not None

    def test_no_error_fields_on_success(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.error_type is None
        assert job.error_message is None


# ==============================================================
# DB書き込み: 失敗ケース
# ==============================================================

@requires_docker
class TestErrorJobRecording:
    def test_job_status_is_error_on_validation_failure(self, data_dirs, db_session):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.status == "error"

    def test_job_error_type_recorded(self, data_dirs, db_session):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.error_type == "ValidationError"

    def test_job_error_message_recorded(self, data_dirs, db_session):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.error_message is not None
        assert len(job.error_message) > 0

    def test_job_output_path_is_null_on_error(self, data_dirs, db_session):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.output_path is None

    def test_xml_syntax_error_recorded(self, data_dirs, db_session):
        xml = data_dirs["input"] / "broken.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_broken_xml.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert job.status == "error"
        assert job.error_type == "ValidationError"


# ==============================================================
# 複数ファイル処理
# ==============================================================

@requires_docker
class TestMultipleFiles:
    def test_multiple_jobs_recorded(self, data_dirs, db_session):
        """複数XMLを処理したとき各ファイル分のジョブが記録される"""
        for i in range(3):
            xml = data_dirs["input"] / f"sample_{i}.xml"
            shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
            run_pipeline_with_db(xml, data_dirs, db_session)

        jobs = db_session.query(ConversionJob).all()
        assert len(jobs) == 3

    def test_mixed_success_and_error_jobs(self, data_dirs, db_session):
        valid = data_dirs["input"] / "valid.xml"
        invalid = data_dirs["input"] / "invalid.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", valid)
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", invalid)

        run_pipeline_with_db(valid, data_dirs, db_session)
        run_pipeline_with_db(invalid, data_dirs, db_session)

        statuses = {j.file_name: j.status for j in db_session.query(ConversionJob).all()}
        assert statuses["valid.xml"] == "success"
        assert statuses["invalid.xml"] == "error"


# ==============================================================
# エンド・ツー・エンド: FHIR JSON の内容検証
# ==============================================================

@requires_docker
class TestFhirOutputContent:
    def test_output_bundle_resource_type(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        json_files = list(data_dirs["output"].glob("*.json"))
        bundle = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert bundle["resourceType"] == "Bundle"

    def test_output_bundle_entry_count(self, data_dirs, db_session):
        """Patient/Organization/Encounter + Observation群が含まれること"""
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        json_files = list(data_dirs["output"].glob("*.json"))
        bundle = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert len(bundle["entry"]) >= 4  # Patient + Org + Encounter + 1以上のObservation

    def test_output_bundle_patient_name(self, data_dirs, db_session):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        json_files = list(data_dirs["output"].glob("*.json"))
        bundle = json.loads(json_files[0].read_text(encoding="utf-8"))
        patient = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        assert "田中" in patient["name"][0]["text"]

    def test_output_json_path_matches_db_record(self, data_dirs, db_session):
        """DB記録のoutput_pathと実際のJSONファイルが一致すること"""
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline_with_db(xml, data_dirs, db_session)

        job = db_session.query(ConversionJob).first()
        assert Path(job.output_path).exists()
