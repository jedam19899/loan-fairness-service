from sqlalchemy import Column, Integer, String, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(String, unique=True, nullable=False)
    features = Column(JSON, nullable=False)
    decision = Column(String, nullable=True)

    def __repr__(self):
        return f"<Application(application_id={self.application_id}, decision={self.decision})>"
