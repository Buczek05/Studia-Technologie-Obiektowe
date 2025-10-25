from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CurrencyRateResponse(BaseModel):
    currency: str = Field(..., description="Currency code (e.g., USD)", examples=["USD"])
    reference_currency: str = Field(..., description="Reference currency code", examples=["PLN"])
    exchange_date: date = Field(..., description="Date of the exchange rate")
    rate: Decimal = Field(..., description="Exchange rate", examples=[3.9876])


class SyncResponse(BaseModel):
    message: str = Field(..., description="Status message")
    start_date: date = Field(..., description="Start date of sync")
    end_date: date = Field(..., description="End date of sync")
    tables_created: int = Field(..., description="Number of exchange tables created")
    rates_created: int = Field(..., description="Number of currency rates created")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
