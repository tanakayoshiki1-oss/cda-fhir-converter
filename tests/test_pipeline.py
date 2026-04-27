import json
import os
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch

SAMPLES_DIR = Path(__file__).parent / "samples"


def run_pipeline(xml_path: Path, data_dirs: dict):
    """環境変数を差し替えて pipeline.convert_file を実行するヘルパー"""
    env = {
        "OUTPUT_DIR": str(data_dirs["output"]),
        "SUCCESS_DIR": str(data_dirs["success"]),
        "ERROR_DIR": str(data_dirs["error"]),
        "LOG_DIR": str(data_dirs["logs"]),
    }
    with patch.dict(os.environ, env):
        # pipeline モジュールはトップレベルで Path を解決するため再インポートで反映
        import importlib
        import src.converter.pipeline as pipeline_mod
        importlib.reload(pipeline_mod)
        pipeline_mod.convert_file(xml_path)


class TestSuccessfulConversion:
    def test_json_created_in_output(self, data_dirs):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)
        assert any(data_dirs["output"].glob("*.json"))

    def test_xml_moved_to_success(self, data_dirs):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)
        assert (data_dirs["success"] / "sample.xml").exists()

    def test_input_xml_removed_from_input(self, data_dirs):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)
        assert not xml.exists()

    def test_output_json_is_valid_json(self, data_dirs):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)
        json_files = list(data_dirs["output"].glob("*.json"))
        assert len(json_files) == 1
        content = json.loads(json_files[0].read_text(encoding="utf-8"))
        assert content["resourceType"] == "Bundle"

    def test_output_json_filename_contains_stem(self, data_dirs):
        xml = data_dirs["input"] / "20240401_test.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)
        json_files = list(data_dirs["output"].glob("*.json"))
        assert any("20240401_test" in f.name for f in json_files)

    def test_no_error_log_on_success(self, data_dirs):
        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)
        assert not any(data_dirs["logs"].glob("*.txt"))


class TestFailedConversion:
    def test_xml_moved_to_error_on_validation_failure(self, data_dirs):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline(xml, data_dirs)
        assert (data_dirs["error"] / "bad.xml").exists()

    def test_error_log_created_on_validation_failure(self, data_dirs):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline(xml, data_dirs)
        assert any(data_dirs["logs"].glob("*_error.txt"))

    def test_no_json_on_failure(self, data_dirs):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline(xml, data_dirs)
        assert not any(data_dirs["output"].glob("*.json"))

    def test_xml_moved_to_error_on_broken_xml(self, data_dirs):
        xml = data_dirs["input"] / "broken.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_broken_xml.xml", xml)
        run_pipeline(xml, data_dirs)
        assert (data_dirs["error"] / "broken.xml").exists()

    def test_error_log_contains_error_type(self, data_dirs):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline(xml, data_dirs)
        log_files = list(data_dirs["logs"].glob("*_error.txt"))
        assert len(log_files) == 1
        content = log_files[0].read_text(encoding="utf-8")
        assert "ValidationError" in content

    def test_error_log_contains_filename(self, data_dirs):
        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline(xml, data_dirs)
        log_files = list(data_dirs["logs"].glob("*_error.txt"))
        content = log_files[0].read_text(encoding="utf-8")
        assert "bad.xml" in content


class TestFileCollision:
    def test_duplicate_filename_in_success_gets_suffix(self, data_dirs):
        # 先に success/ に同名ファイルを置く
        (data_dirs["success"] / "sample.xml").write_text("existing", encoding="utf-8")

        xml = data_dirs["input"] / "sample.xml"
        shutil.copy(SAMPLES_DIR / "sample_tokutei_kenshin.xml", xml)
        run_pipeline(xml, data_dirs)

        success_files = list(data_dirs["success"].glob("sample*.xml"))
        assert len(success_files) == 2

    def test_duplicate_filename_in_error_gets_suffix(self, data_dirs):
        # 先に error/ に同名ファイルを置く
        (data_dirs["error"] / "bad.xml").write_text("existing", encoding="utf-8")

        xml = data_dirs["input"] / "bad.xml"
        shutil.copy(SAMPLES_DIR / "sample_invalid_no_template.xml", xml)
        run_pipeline(xml, data_dirs)

        error_files = list(data_dirs["error"].glob("bad*.xml"))
        assert len(error_files) == 2
