from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any


class SensorData(BaseModel):
    user_id: str
    session_id: str
    timestamp: datetime
    heart_rate: int
    spo2: int
    steps: int
    sleep_hours: float
    stress_level: int
    session_type: str = "daily_check"


class CSIOutput(BaseModel):
    csi_score: int
    risk_level: str
    drivers: List[str]
    recommendations: List[str]
    baseline_comparison: Dict[str, Any]
    model_version: str