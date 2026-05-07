from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from datetime import datetime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    password_hash = Column(String)
    age_range = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SensorSession(Base):
    __tablename__ = "sensor_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    session_type = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    user_id = Column(String, index=True)
    timestamp = Column(DateTime)
    heart_rate = Column(Integer)
    spo2 = Column(Integer)
    steps = Column(Integer)
    sleep_hours = Column(Float)
    stress_level = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class CSIResult(Base):
    __tablename__ = "csi_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime)

    csi_score = Column(Integer)
    risk_level = Column(String)
    drivers = Column(JSON)
    recommendations = Column(JSON)
    baseline_comparison = Column(JSON)
    model_version = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)