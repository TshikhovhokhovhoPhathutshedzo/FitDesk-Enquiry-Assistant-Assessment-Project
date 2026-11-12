from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class Intent(str, Enum):
    PRICING = "pricing"
    AVAILABILITY = "availability"
    PRICING_AND_AVAILABILITY = "pricing_and_availability"
    OTHER = "other"


class EnquiryAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: Intent
    details: str = Field(default="")
    packages: list[str] = Field(default_factory=list)
    saturday_times: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True
