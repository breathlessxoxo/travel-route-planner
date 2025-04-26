from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class BudgetLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class GenerateRouteRequest(BaseModel):
    destination: str = Field(..., description="目的地城市")
    days: int = Field(..., ge=1, le=14, description="旅行天数")
    budget: BudgetLevel = Field(..., description="预算等级")
    people: int = Field(..., ge=1, le=10, description="出行人数")

class AttractionResponse(BaseModel):
    name: str
    visit_order: int

class DayPlan(BaseModel):
    day: int
    attractions: List[AttractionResponse]
    hotel: str
    total_drive_time: float

class GenerateRouteResponse(BaseModel):
    status: str = "success"
    data: List[DayPlan]
    raw_ai_response: str

class ValidateRouteRequest(BaseModel):
    days: List[DayPlan]
    raw_ai_response: str

class ValidateRouteResponse(BaseModel):
    is_valid: bool
    invalid_days: List[int] 