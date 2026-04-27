import subprocess
import time
import pytest
import docker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.db.models import Base

PG_CONTAINER_NAME = "cda-fhir-test-postgres"
PG_PORT = 15432
PG_PASSWORD = "testpass"
PG_DB = "cda_fhir_test"
PG_USER = "testuser"
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@localhost:{PG_PORT}/{PG_DB}"


def is_docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


requires_docker = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker が起動していません。Docker Desktop を起動してから再実行してください。",
)


def _start_postgres():
    """docker run でPostgreSQLコンテナを起動"""
    subprocess.run(
        ["docker", "rm", "-f", PG_CONTAINER_NAME],
        capture_output=True,
    )
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", PG_CONTAINER_NAME,
            "-e", f"POSTGRES_PASSWORD={PG_PASSWORD}",
            "-e", f"POSTGRES_USER={PG_USER}",
            "-e", f"POSTGRES_DB={PG_DB}",
            "-p", f"{PG_PORT}:5432",
            "postgres:15",
        ],
        check=True,
        capture_output=True,
    )


def _wait_for_postgres(timeout=60):
    """PostgreSQLが接続受付するまで待機"""
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            return
        except Exception:
            time.sleep(2)
    engine.dispose()
    raise TimeoutError("PostgreSQL did not become ready in time")


def _stop_postgres():
    subprocess.run(
        ["docker", "rm", "-f", PG_CONTAINER_NAME],
        capture_output=True,
    )


@pytest.fixture(scope="session")
def pg_container():
    _start_postgres()
    _wait_for_postgres()
    yield
    _stop_postgres()


@pytest.fixture(scope="session")
def db_engine(pg_container):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """各テストに独立したセッションを提供し、テスト後にロールバック"""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
