import json
import logging
import os
import shutil
import traceback
from datetime import datetime
from pathlib import Path

from src.converter.cda_parser import CdaParser, ValidationError
from src.converter.fhir_builder import FhirBundleBuilder

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "data/output"))
SUCCESS_DIR = Path(os.getenv("SUCCESS_DIR", "data/success"))
ERROR_DIR = Path(os.getenv("ERROR_DIR", "data/error"))
LOG_DIR = Path(os.getenv("LOG_DIR", "data/logs"))


def convert_file(xml_path: Path):
    logger.info(f"Processing: {xml_path.name}")
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    try:
        parser = CdaParser(xml_path)
        parser.validate()
        cda_data = parser.parse()

        builder = FhirBundleBuilder(cda_data)
        bundle = builder.build()

        output_name = f"{xml_path.stem}_{timestamp}.json"
        output_path = OUTPUT_DIR / output_name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        _move_file(xml_path, SUCCESS_DIR)
        logger.info(f"Conversion success: {xml_path.name} → {output_path.name}")

    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Conversion failed: {xml_path.name} - {error_type}: {e}")
        _write_error_log(xml_path, timestamp, error_type, e)
        _move_file(xml_path, ERROR_DIR)


def _move_file(src: Path, dest_dir: Path):
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if dest.exists():
        stem = src.stem
        suffix = src.suffix
        i = 1
        while dest.exists():
            dest = dest_dir / f"{stem}_{i}{suffix}"
            i += 1
    shutil.move(str(src), str(dest))


def _write_error_log(xml_path: Path, timestamp: str, error_type: str, exc: Exception):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_name = f"{xml_path.stem}_{timestamp}_error.txt"
    log_path = LOG_DIR / log_name

    content = f"""\
=== CDA FHIR Converter - Error Report ===
File       : {xml_path.name}
Timestamp  : {timestamp}
Error Type : {error_type}
Message    : {exc}

Stack Trace:
{traceback.format_exc()}
"""
    log_path.write_text(content, encoding="utf-8")
