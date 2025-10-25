from datetime import date, timedelta
from typing import Any

import requests
from loguru import logger
from sqlmodel import Session, select

from app.external_api.nbp.dto import NBP_DEFAULT_CURRENCY, NBPDateResponseDTO
from app.models import CurrencyRate, ExchangeTable


class NBPCurrencyApiDownloader:
    BASE_URL_TEMPLATE = "https://api.nbp.pl/api/exchangerates/tables/%(table)s/%(start_date)s/%(end_date)s/"
    TABLES = ["A", "B"]

    def __init__(self, session: Session, start_date: date, end_date: date) -> None:
        self.session = session
        self.exchange_tables: list[ExchangeTable] = []
        self.currency_rates: list[CurrencyRate] = []
        self.start_date = start_date
        self.end_date = end_date
        self.new_date: date
        self.last_date: date
        self.download_data: list[NBPDateResponseDTO]
        self.download_data_dict: dict[date, NBPDateResponseDTO]
        self.existing_exchange_tables: dict[date, ExchangeTable]

    def download_and_save_data(self) -> None:
        self._download_and_setup_data()
        self._setup_existing_exchange_tables()
        self._prepare_objects()
        self._save_objects_to_db()

    def _download_and_setup_data(self) -> None:
        all_data: list[Any] = []
        for table in self.TABLES:
            url = self.BASE_URL_TEMPLATE % {
                "table": table,
                "start_date": self.start_date,
                "end_date": self.end_date,
            }
            response = requests.get(url)
            logger.info(
                f"Downloaded data from NBP API table {table}. Status code: {response.status_code}. "
                f"Data: {response.json()}"
            )
            response.raise_for_status()
            all_data.extend(response.json())

        self.download_data = [NBPDateResponseDTO.model_validate(date_response) for date_response in all_data]
        self.download_data_dict = {}
        for date_response in self.download_data:
            if date_response.effectiveDate in self.download_data_dict:
                self.download_data_dict[date_response.effectiveDate].rates.extend(date_response.rates)
            else:
                self.download_data_dict[date_response.effectiveDate] = date_response

    def _setup_existing_exchange_tables(self) -> None:
        statement = select(ExchangeTable).where(
            ExchangeTable.exchange_date >= self.start_date,
            ExchangeTable.exchange_date <= self.end_date,
            ExchangeTable.reference_currency == NBP_DEFAULT_CURRENCY,
        )
        objects = self.session.exec(statement).all()
        self.existing_exchange_tables = {obj.exchange_date: obj for obj in objects}

    def _prepare_objects(self) -> None:
        self.new_date = self.last_date = min(self.download_data_dict.keys())
        while self.new_date <= self.end_date:
            if self.new_date in self.existing_exchange_tables:
                self._add_objects_for_exist_exchange_table()
            else:
                self._add_objects_for_new_exchange_table()
            self._setup_next_dates()

    def _add_objects_for_exist_exchange_table(self) -> None:
        exchange_table = self.existing_exchange_tables[self.new_date]
        rates = self._get_day_download_data().rates
        self.currency_rates.extend([rate_dto.to_object(exchange_table) for rate_dto in rates])

    def _add_objects_for_new_exchange_table(self) -> None:
        exchange_table, currency_objects = self._get_day_download_data().to_objects(self.new_date)
        self.exchange_tables.append(exchange_table)
        self.currency_rates.extend(currency_objects)

    def _get_day_download_data(self) -> NBPDateResponseDTO:
        return self.download_data_dict.get(self.new_date) or self.download_data_dict[self.last_date]

    def _setup_next_dates(self) -> None:
        self.last_date = self.new_date if self.new_date in self.download_data_dict else self.last_date
        self.new_date += timedelta(days=1)

    def _save_objects_to_db(self) -> None:
        for exchange_table in self.exchange_tables:
            self.session.add(exchange_table)
        self.session.flush()

        for exchange_table in self.exchange_tables:
            for rate in self.currency_rates:
                if rate.exchange_table == exchange_table:
                    if exchange_table.id is not None:
                        rate.exchange_table_id = exchange_table.id

        for rate in self.currency_rates:
            existing = self.session.exec(
                select(CurrencyRate).where(
                    CurrencyRate.exchange_table_id == rate.exchange_table_id,
                    CurrencyRate.currency == rate.currency,
                )
            ).first()
            if not existing:
                self.session.add(rate)

        self.session.commit()
        logger.debug(
            f"Saved {len(self.exchange_tables)} exchange tables and {len(self.currency_rates)} rates to database."
        )
