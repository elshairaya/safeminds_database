from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any


class SensorData(BaseModel):
    user_id: str
    # For validation, support both backend snake_case and mobile camelCase 
    # ( check which one is needed after knowing the final JSON)
    session_id: Optional[str] = None
    sessionId: Optional[str] = None
    timestamp: datetime
    # check also which one is used in mobile
    session_type: Optional[str] = None
    sessionType: Optional[str] = None
    
    session_start: Optional[datetime] = None
    sessionStart: Optional[datetime] = None
    
    session_end: Optional[datetime] = None
    sessionEnd: Optional[datetime] = None
    
    hr_mean: Optional[float] = None
    hrMean: Optional[float] = None
    
    hr_min: Optional[float] = None
    hrMin: Optional[float] = None
    
    hr_max: Optional[float] = None
    hrMax: Optional[float] = None
    
    movement_mean: Optional[float] = None
    movementMean: Optional[float] = None

    movement_variance: Optional[float] = None
    movementVariance: Optional[float] = None

    total_epochs: Optional[int] = None
    totalEpochs: Optional[int] = None

    # mobile profile fields
    age: Optional[float] = None
    gender: Optional[float] = None
    bmi: Optional[float] = None

    # mobile questionnaire fields
    insomnia_score: Optional[float] = None
    insomniaScore: Optional[float] = None

    sleepiness_score: Optional[float] = None
    sleepinessScore: Optional[float] = None

    chronotype_score: Optional[float] = None
    chronotypeScore: Optional[float] = None

    

class CSIOutput(BaseModel):
    csi_score: int
    risk_level: str
    drivers: List[str]
    recommendations: List[str]
    baseline_comparison: Dict[str, Any]
    model_version: str

class UserSignup(BaseModel):
    username: str
    full_name: str
    password: str
    age_range: str
    gender: str

class UserLogin(BaseModel):
    username: str
    password: str