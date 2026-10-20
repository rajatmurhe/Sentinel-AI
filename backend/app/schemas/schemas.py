from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any, Literal

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "User"

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ActivityCreate(BaseModel):
    action_type: str
    bytes_transferred: float = 0.0
    is_sensitive_file: bool = False
    failed_attempts: int = 0
    privilege_level: int = 0
    session_duration_sec: float = 0.0

class ActivityOut(BaseModel):
    id: int
    user_id: int
    timestamp: datetime
    action_type: str
    bytes_transferred: float
    is_sensitive_file: bool
    failed_attempts: int
    class Config:
        from_attributes = True

class TelemetryVector(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid")
    login_hour: float = Field(ge=0, lt=24)
    files_accessed: float = Field(ge=0, le=1e6)
    sensitive_files_accessed: float = Field(ge=0, le=1e6)
    bytes_transferred_mb: float = Field(ge=0, le=1e9)
    failed_logins: float = Field(ge=0, le=1e6)
    privilege_level: float = Field(ge=0, le=2)
    session_duration_min: float = Field(ge=0, le=1440)

class SimulationTrigger(BaseModel):
    user_id: int = Field(ge=1)
    scenario: Literal["NORMAL", "DATA_EXFILTRATION", "ABNORMAL_HOURS", "ADAPTIVE_EVASION"]
    iterations: int = Field(default=8, ge=1, le=50)
    seed: int = Field(default=0, ge=0, le=2147483647)

class AnalysisResponse(BaseModel):
    user_id: int
    risk_score: float
    iforest_anomaly: bool
    ocsvm_anomaly: bool
    game_action: str
    top_explanations: dict[str, float]
    details: dict[str, Any]
    adaptive_metrics: dict[str, Any]