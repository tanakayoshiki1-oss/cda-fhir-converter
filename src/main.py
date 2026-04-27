import logging
import os
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

from src.watcher.scheduler import run_conversion_job
from src.db.models import get_session_factory

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    interval = int(os.getenv("WATCH_INTERVAL_SECONDS", "300"))

    session_factory = None
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        logger.info("Database connected. Job tracking enabled.")
        session_factory = get_session_factory(database_url)
    else:
        logger.warning("DATABASE_URL not set. Running without job tracking.")

    logger.info(f"CDA FHIR Converter started. Watch interval: {interval}s")

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_conversion_job, "interval", seconds=interval, args=[session_factory]
    )

    run_conversion_job(session_factory)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Converter stopped.")


if __name__ == "__main__":
    main()
