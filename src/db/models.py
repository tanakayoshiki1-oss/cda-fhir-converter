from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")


class Base(DeclarativeBase):
    pass


class ConversionJob(Base):
    __tablename__ = "conversion_jobs"

    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_type = Column(String(100))
    error_message = Column(Text)
    output_path = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, file_name: str, file_path: str) -> ConversionJob:
        job = ConversionJob(
            file_name=file_name,
            file_path=file_path,
            status="processing",
            started_at=datetime.now(),
        )
        self.session.add(job)
        self.session.commit()
        return job

    def mark_success(self, job: ConversionJob, output_path: str):
        job.status = "success"
        job.completed_at = datetime.now()
        job.output_path = output_path
        self.session.commit()

    def mark_error(self, job: ConversionJob, error_type: str, error_message: str):
        job.status = "error"
        job.completed_at = datetime.now()
        job.error_type = error_type
        job.error_message = error_message
        self.session.commit()


def get_engine(url: str = ""):
    return create_engine(url or DATABASE_URL)


def get_session_factory(url: str = ""):
    engine = get_engine(url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
