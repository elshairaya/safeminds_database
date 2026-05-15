from pydantic import BaseModel,Field, ConfigDict
from typing import List, Optional, Dict, Any


class SensorData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)  
    user_id: str = Field(alias="userID")
    # For validation, support both backend snake_case and mobile camelCase 
    # ( check which one is needed after knowing the final JSON)
    session_id: str = Field(alias="dataID")
    timestamp: int = Field(alias="timeStamp")

    # check also which one is used in mobile
   # session_type: str = Field(alias="sessionType")

   #this one is added by shahed to enable testing
    session_start: Optional[str] = Field(default=None ,alias="sessionStart")
    session_end: Optional[str] = Field(default=None ,alias="sessionEnd")


    hr_mean: Optional[float] = Field(default=None, alias="hrMean")
    hr_min: Optional[float] = Field(default=None, alias="hrMin")
    hr_max: Optional[float] = Field(default=None, alias="hrMax")

    movement_mean: Optional[float] = Field(default=None, alias="movementMean")
    movement_variance: Optional[float] = Field(default=None, alias="movementVariance")

    total_epochs: Optional[int] = Field(default=None, alias="totalEpochs")
       
    # mobile profile fields
    age: Optional[float] = None
    gender: Optional[str] = None
    bmi: Optional[float] = None
    # mobile questionnaire fields
    insomnia_score: Optional[float] = Field(default=None, alias="insomniaScore")
    sleepiness_score: Optional[float] = Field(default=None, alias="sleepinessScore")
    chronotype_score: Optional[float] = Field(default=None, alias="chronotypeScore")

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

    #added by shahed
    height:Optional[float]=None
    weight:Optional[float]=None

class UserLogin(BaseModel):
    username: str
    password: str