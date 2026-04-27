import logging
import os
from pathlib import Path

from src.converter.pipeline import convert_file

logger = logging.getLogger(__name__)

INPUT_DIR = Path(os.getenv("INPUT_DIR", "data/input"))


def run_conversion_job():
    logger.info(f"Scanning: {INPUT_DIR}")
    xml_files = sorted(INPUT_DIR.glob("*.xml"))

    if not xml_files:
        logger.info("No XML files found.")
        return

    logger.info(f"Found {len(xml_files)} file(s).")
    for xml_path in xml_files:
        convert_file(xml_path)
