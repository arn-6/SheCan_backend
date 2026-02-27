from pydantic import BaseModel, Field
from typing import List, Optional


class FertilityRiskInput(BaseModel):
    age: int = Field(..., ge=13, le=55, description="Patient age")
    cancer_type: str = Field(..., description="Type of cancer")
    cancer_stage: str = Field(..., description="Cancer stage")
    amh_level: float = Field(..., ge=0.0, le=15.0, description="AMH level in ng/mL")
    medical_conditions: List[str] = Field(default=[], description="Pre-existing conditions")
    period_regularity: str = Field(..., description="Menstrual regularity")
    bmi: Optional[float] = Field(default=22.0, ge=10.0, le=60.0)
    smoking: Optional[bool] = Field(default=False)
    previous_pregnancies: Optional[int] = Field(default=0, ge=0)


class TechniqueInput(BaseModel):
    age: int = Field(..., ge=13, le=55)
    cancer_type: str
    cancer_stage: str
    city: str
    has_partner: bool = False
    needs_immediate_treatment: bool = False
    storage_years: int = Field(default=5, ge=1, le=20)
    amh_level: Optional[float] = Field(default=2.0, ge=0.0, le=15.0)