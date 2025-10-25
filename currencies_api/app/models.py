from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class ExchangeTable(SQLModel, table=True):
    __tablename__ = "exchange_table"

    id: Optional[int] = Field(default=None, primary_key=True)
    exchange_date: date = Field(index=True)
    reference_currency: str = Field(max_length=3, default="PLN", index=True)
    currency_rates: list["CurrencyRate"] = Relationship(back_populates="exchange_table")


class CurrencyRate(SQLModel, table=True):
    __tablename__ = "currency_rate"

    id: Optional[int] = Field(default=None, primary_key=True)
    exchange_table_id: int = Field(foreign_key="exchange_table.id", index=True)
    currency: str = Field(max_length=3, index=True)
    mid: Decimal = Field(max_digits=10, decimal_places=4)
    exchange_table: Optional[ExchangeTable] = Relationship(back_populates="currency_rates")
