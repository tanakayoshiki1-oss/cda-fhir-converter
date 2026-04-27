import logging
import os
from pathlib import Path

from src.converter.pipeline import convert_file

logger = logging.getLogger(__name__)

INPUT_DIR = Path(os.getenv("INPUT_DIR", "data/input"))


def run_conversion_job(session_factory=None):
    logger.info(f"Scanning: {INPUT_DIR}")
    xml_files = sorted(INPUT_DIR.glob("*.xml"))

    if not xml_files:
        logger.info("No XML files found.")
        return

    logger.info(f"Found {len(xml_files)} file(s).")
    for xml_path in xml_files:
        if session_factory:
            session = session_factory()
            try:
                convert_file(xml_path, db_session=session)
            finally:
                session.close()
        else:
            convert_file(xml_path)
