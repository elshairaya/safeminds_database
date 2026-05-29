from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)

    username = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    password_hash = Column(String)

    age_range = Column(String, nullable=True)
    gender = Column(String, nullable=True)

    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    sensor_sessions = relationship(
        "SensorSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    sensor_readings = relationship(
        "SensorReading",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    csi_results = relationship(
        "CSIResult",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class SensorSession(Base):
    __tablename__ = "sensor_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)

    user_id = Column(
        String,
        ForeignKey("users.user_id"),
        index=True,
        nullable=False
    )

    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    session_type = Column(String)
    status = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="sensor_sessions"
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        String,
        ForeignKey("users.user_id"),
        index=True,
        nullable=False
    )

    session_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    timestamp = Column(DateTime)

    session_type = Column(String, nullable=True)
    session_start = Column(DateTime, nullable=True)
    session_end = Column(DateTime, nullable=True)

    hr_mean = Column(Float, nullable=True)
    hr_min = Column(Float, nullable=True)
    hr_max = Column(Float, nullable=True)

    movement_mean = Column(Float, nullable=True)
    movement_variance = Column(Float, nullable=True)
    total_epochs = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="sensor_readings"
    )

    csi_result = relationship(
        "CSIResult",
        back_populates="sensor_reading",
        uselist=False,
        cascade="all, delete-orphan"
    )


class CSIResult(Base):
    __tablename__ = "csi_results"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        String,
        ForeignKey("users.user_id"),
        index=True,
        nullable=False
    )

    session_id = Column(
        String,
        ForeignKey("sensor_readings.session_id"),
        index=True,
        nullable=False
    )

    timestamp = Column(DateTime)

    csi_score = Column(Integer)
    risk_level = Column(String)
    drivers = Column(JSON)
    recommendations = Column(JSON)
    baseline_comparison = Column(JSON)
    model_version = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="csi_results"
    )

    sensor_reading = relationship(
        "SensorReading",
        back_populates="csi_result"
    )