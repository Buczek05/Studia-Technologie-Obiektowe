# Currency Exchange Rate API

FastAPI application for retrieving currency exchange rates from the National Bank of Poland (NBP) API.

## Features

- Fetch exchange rates for specific currencies and dates
- Download and cache historical data from NBP API
- SQLite database storage
- RESTful API with automatic documentation

## Project Structure

```
currencies_api/
├── app/
│   ├── main.py              # FastAPI application and endpoints
│   ├── models.py            # SQLModel database models
│   ├── database.py          # Database connection setup
│   ├── repository.py        # Data access layer
│   ├── schemas.py           # Pydantic request/response schemas
│   └── external_api/
│       └── nbp/
│           ├── dto.py       # NBP API DTOs
│           └── downloader.py # NBP API downloader
├── pyproject.toml           # Project dependencies (uv)
└── currencies.db            # SQLite database (auto-created)
```

## Installation

1. Install dependencies using uv:
```bash
uv sync
```

## Running the API

Start the development server:
```bash
uv run uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### 1. Get Currency Rate

Get exchange rate for a specific currency and date.

```
GET /api/currency/rate?currency=USD&exchange_date=2025-10-25&reference_currency=PLN
```

**Parameters:**
- `currency` (required): Currency code (e.g., USD, EUR)
- `exchange_date` (required): Date in YYYY-MM-DD format
- `reference_currency` (optional): Reference currency code (default: PLN)

**Response:**
```json
{
  "currency": "USD",
  "reference_currency": "PLN",
  "exchange_date": "2025-10-25",
  "rate": 3.9876
}
```

### 2. Sync Data

Download and store currency data from NBP API.

```
POST /api/sync?start_date=2025-10-20&end_date=2025-10-25
```

**Parameters:**
- `start_date` (required): Start date in YYYY-MM-DD format
- `end_date` (required): End date in YYYY-MM-DD format

**Response:**
```json
{
  "message": "Data synchronized successfully",
  "start_date": "2025-10-20",
  "end_date": "2025-10-25",
  "tables_created": 5,
  "rates_created": 250
}
```

## Usage Example

1. **Start the server:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```

2. **Sync data for a date range:**
   ```bash
   curl -X POST "http://localhost:8000/api/sync?start_date=2025-10-20&end_date=2025-10-25"
   ```

3. **Get exchange rate:**
   ```bash
   curl "http://localhost:8000/api/currency/rate?currency=USD&exchange_date=2025-10-25"
   ```

## Database

The application uses SQLite with two main tables:

- `exchange_table`: Stores exchange rate tables by date and reference currency
- `currency_rate`: Stores individual currency rates

## Architecture

The application follows a layered architecture:

1. **Interface Layer** (FastAPI endpoints in `main.py`)
2. **Repository Layer** (`repository.py`)
3. **Database Layer** (SQLModel models in `models.py`)
4. **External API Layer** (NBP API integration in `external_api/nbp/`)

## Dependencies

- **FastAPI**: Web framework
- **SQLModel**: SQL database ORM
- **Uvicorn**: ASGI server
- **Requests**: HTTP client for NBP API
- **Loguru**: Logging
- **Pydantic**: Data validation
