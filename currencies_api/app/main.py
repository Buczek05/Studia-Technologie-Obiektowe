from datetime import date
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Query
from loguru import logger
from sqlmodel import Session

from app.database import create_db_and_tables, get_session
from app.external_api.nbp.downloader import NBPCurrencyApiDownloader
from app.repository import CurrencyRepository
from app.schemas import CurrencyRateResponse, ErrorResponse, SyncResponse

app = FastAPI(
    title="Currency Exchange Rate API",
    description="API for retrieving currency exchange rates from NBP (National Bank of Poland)",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    logger.info("Database tables created/verified")


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Currency Exchange Rate API",
        "version": "0.1.0",
        "endpoints": {
            "get_rate": "/api/currency/rate",
            "sync_data": "/api/sync",
            "docs": "/docs",
        },
    }


@app.get(
    "/api/currency/rate",
    response_model=CurrencyRateResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
def get_currency_rate(
    currency: Annotated[str, Query(description="Currency code (e.g., USD, EUR)", examples=["USD"])],
    exchange_date: Annotated[date, Query(description="Date for exchange rate", examples=["2025-10-25"])],
    reference_currency: Annotated[str, Query(description="Reference currency code", examples=["PLN"])] = "PLN",
    session: Session = Depends(get_session),
) -> CurrencyRateResponse:
    logger.info(f"GET rate request: {currency}/{reference_currency} on {exchange_date}")

    if len(currency) != 3 or not currency.isalpha():
        raise HTTPException(status_code=400, detail="Invalid currency code. Must be 3 letters.")

    if len(reference_currency) != 3 or not reference_currency.isalpha():
        raise HTTPException(status_code=400, detail="Invalid reference currency code. Must be 3 letters.")

    repository = CurrencyRepository(session)
    rate = repository.get_rate_by_date(
        currency=currency.upper(),
        reference_currency=reference_currency.upper(),
        exchange_date=exchange_date,
    )

    if rate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Exchange rate not found for {currency}/{reference_currency} on {exchange_date}",
        )

    return CurrencyRateResponse(
        currency=currency.upper(),
        reference_currency=reference_currency.upper(),
        exchange_date=exchange_date,
        rate=rate,
    )


@app.post(
    "/api/sync",
    response_model=SyncResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def sync_currency_data(
    start_date: Annotated[date, Query(description="Start date for data sync", examples=["2025-10-20"])],
    end_date: Annotated[date, Query(description="End date for data sync", examples=["2025-10-25"])],
    session: Session = Depends(get_session),
) -> SyncResponse:
    logger.info(f"POST sync request: {start_date} to {end_date}")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")

    if (end_date - start_date).days > 31:
        raise HTTPException(status_code=400, detail="Date range too large. Maximum 31 days allowed.")

    try:
        downloader = NBPCurrencyApiDownloader(session, start_date, end_date)

        downloader.download_and_save_data()

        tables_created = len(downloader.exchange_tables)
        rates_created = len(downloader.currency_rates)

        logger.info(f"Sync completed: {tables_created} tables, {rates_created} rates")

        return SyncResponse(
            message="Data synchronized successfully",
            start_date=start_date,
            end_date=end_date,
            tables_created=tables_created,
            rates_created=rates_created,
        )

    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync data: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
