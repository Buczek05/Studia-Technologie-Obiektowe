from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import CurrencyRate, ExchangeTable

NBP_DEFAULT_CURRENCY = "PLN"


class NBPRateResponseDTO(BaseModel):
    code: str = Field(..., description="Currency code (e.g., USD, EUR)")
    currency: str = Field(..., description="Full currency name")
    mid: Decimal = Field(..., description="Mid exchange rate")

    def to_object(self, exchange_table: ExchangeTable) -> CurrencyRate:
        return CurrencyRate(
            exchange_table_id=exchange_table.id,
            currency=self.code,
            mid=self.mid,
        )


class NBPDateResponseDTO(BaseModel):
    effectiveDate: date = Field(..., description="Effective date of exchange rates")
    rates: list[NBPRateResponseDTO] = Field(..., description="List of currency rates")

    def to_objects(self, exchange_date: date) -> tuple[ExchangeTable, list[CurrencyRate]]:
        exchange_table = ExchangeTable(
            exchange_date=exchange_date,
            reference_currency=NBP_DEFAULT_CURRENCY,
        )

        currency_rates = [rate_dto.to_object(exchange_table) for rate_dto in self.rates]

        return exchange_table, currency_rates
