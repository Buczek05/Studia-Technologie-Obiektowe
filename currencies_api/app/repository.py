from datetime import date
from decimal import Decimal
from typing import Optional

from loguru import logger
from sqlmodel import Session, col, select

from app.models import CurrencyRate, ExchangeTable


class CurrencyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_rate_by_date(
        self,
        currency: str,
        reference_currency: str,
        exchange_date: date,
    ) -> Optional[Decimal]:
        logger.debug(
            f"Fetching rate for {currency}/{reference_currency} on {exchange_date}"
        )

        exchange_table_statement = select(ExchangeTable).where(
            ExchangeTable.exchange_date == exchange_date,
            ExchangeTable.reference_currency == reference_currency,
        )
        exchange_table = self.session.exec(exchange_table_statement).first()

        if not exchange_table:
            logger.warning(
                f"No exchange table found for {reference_currency} on {exchange_date}"
            )
            return None

        rate_statement = select(CurrencyRate).where(
            CurrencyRate.exchange_table_id == exchange_table.id,
            CurrencyRate.currency == currency,
        )
        currency_rate = self.session.exec(rate_statement).first()

        if not currency_rate:
            logger.warning(
                f"No rate found for {currency} on {exchange_date}"
            )
            return None

        logger.debug(f"Found rate: {currency_rate.mid}")
        return currency_rate.mid

    def get_latest_rate(
        self,
        currency: str,
        reference_currency: str,
    ) -> Optional[tuple[Decimal, date]]:
        logger.debug(f"Fetching latest rate for {currency}/{reference_currency}")

        exchange_table_statement = (
            select(ExchangeTable)
            .where(ExchangeTable.reference_currency == reference_currency)
            .order_by(col(ExchangeTable.exchange_date).desc())
            .limit(1)
        )
        exchange_table = self.session.exec(exchange_table_statement).first()

        if not exchange_table:
            logger.warning(f"No exchange tables found for {reference_currency}")
            return None

        rate_statement = select(CurrencyRate).where(
            CurrencyRate.exchange_table_id == exchange_table.id,
            CurrencyRate.currency == currency,
        )
        currency_rate = self.session.exec(rate_statement).first()

        if not currency_rate:
            logger.warning(
                f"No rate found for {currency} in latest exchange table"
            )
            return None

        logger.debug(
            f"Found latest rate: {currency_rate.mid} on {exchange_table.exchange_date}"
        )
        return currency_rate.mid, exchange_table.exchange_date
