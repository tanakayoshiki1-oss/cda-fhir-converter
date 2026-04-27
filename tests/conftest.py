from pathlib import Path
import pytest
from src.converter.cda_parser import CdaParser

SAMPLES_DIR = Path(__file__).parent / "samples"


@pytest.fixture
def valid_xml_path():
    return SAMPLES_DIR / "sample_tokutei_kenshin.xml"


@pytest.fixture
def no_template_xml_path():
    return SAMPLES_DIR / "sample_invalid_no_template.xml"


@pytest.fixture
def broken_xml_path():
    return SAMPLES_DIR / "sample_invalid_broken_xml.xml"


@pytest.fixture
def parsed_cda(valid_xml_path):
    parser = CdaParser(valid_xml_path)
    parser.validate()
    return parser.parse()


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
