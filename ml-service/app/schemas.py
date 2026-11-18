from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    CASH_OUT = "CASH_OUT"
    PAYMENT = "PAYMENT"
    CASH_IN = "CASH_IN"


class PredictRequest(BaseModel):
    type: TransactionType
    amount: float = Field(gt=0)
    oldbalanceOrg: float = Field(ge=0)
    oldbalanceDest: float = Field(default=0.0, ge=0)


class PredictResponse(BaseModel):
    score: float = Field(ge=0, le=1)
    modelVersion: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    modelVersion: str | None = None