import logging
import os
import time
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

from src.watcher.scheduler import run_conversion_job

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    interval = int(os.getenv("WATCH_INTERVAL_SECONDS", "300"))
    logger.info(f"CDA FHIR Converter started. Watch interval: {interval}s")

    scheduler = BlockingScheduler()
    scheduler.add_job(run_conversion_job, "interval", seconds=interval)

    # 起動直後に1回実行
    run_conversion_job()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Converter stopped.")


if __name__ == "__main__":
    main()
