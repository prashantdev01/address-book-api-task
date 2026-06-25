# Address Book API

A RESTful address book API built with **FastAPI**, **SQLAlchemy 2.0 (async)**, and **SQLite**.

---

## Features

- Full CRUD on addresses with UUID primary keys
- Coordinate validation via Pydantic v2 (`latitude`, `longitude` range enforcement)
- Geospatial distance search using the **Haversine formula**
- Pagination (`offset` / `limit`) and partial-match `search` on list endpoint
- Unique constraint on coordinates — prevents duplicate addresses
- Idempotency key support — prevents duplicate submissions on retries
- API Key authentication via `X-API-Key` header
- Async database access with `aiosqlite`
- Structured JSON logging via `structlog` (pretty console in debug mode)
- Standard response envelope: `{ data, message, status }`
- Auto-generated Swagger UI and ReDoc

---

## Requirements

- Python 3.11+

---

## Setup

```bash
git clone <repo-url>
cd address-book

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

### Environment variables (`.env`)

| Variable               | Default                                    | Description                        |
|------------------------|--------------------------------------------|------------------------------------|
| `APP_NAME`             | `Address Book API`                         | Application name shown in docs     |
| `APP_VERSION`          | `1.0.0`                                    | Application version                |
| `DEBUG`                | `false`                                    | Enables pretty logs and SQL echo   |
| `DATABASE_URL`         | `sqlite+aiosqlite:///./address_book.db`    | SQLAlchemy async database URL      |
| `LOG_LEVEL`            | `INFO`                                     | `DEBUG / INFO / WARNING / ERROR`   |
| `API_KEY`              | `changeme-secret-key`                      | API key for `X-API-Key` header     |
| `PAGINATION_MAX_LIMIT` | `500`                                      | Maximum allowed page size          |

---

## Run

```bash
uvicorn app.main:app --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | **Swagger UI** (interactive, use this to test) |
| `http://localhost:8000/redoc` | ReDoc (read-only docs) |
| `http://localhost:8000/health` | Health check (no auth required) |

---

## Authentication

All `/addresses` endpoints require an `X-API-Key` header.

**In Swagger UI:**
1. Click the **Authorize** button (top right)
2. Enter the API key (default: `changeme-secret-key`)
3. Click **Authorize** — all requests will now include the header automatically

**In curl:**
```bash
curl -X GET "http://localhost:8000/addresses/" \
     -H "X-API-Key: changeme-secret-key"
```

> Set your own key in `.env`: `API_KEY=your-secret-key-here`

---

## Run Tests

```bash
pytest -v          # run all tests
pytest -s -v       # run with live terminal output (logs + print statements visible)
pytest -s -v -k "nearby"   # run only tests matching a keyword
```

22 tests covering CRUD, validation, distance search, pagination, authentication, and idempotency.

---

## API Reference

| Method   | Endpoint                | Auth | Description                             |
|----------|-------------------------|------|-----------------------------------------|
| `GET`    | `/health`               | No   | Health check                            |
| `POST`   | `/addresses/`           | Yes  | Create a new address                    |
| `GET`    | `/addresses/`           | Yes  | List addresses (paginated + searchable) |
| `GET`    | `/addresses/{id}`       | Yes  | Get a single address by UUID            |
| `PATCH`  | `/addresses/{id}`       | Yes  | Partially update an address             |
| `DELETE` | `/addresses/{id}`       | Yes  | Delete an address                       |
| `GET`    | `/addresses/nearby`     | Yes  | Find addresses within a given distance  |

---

## Address Payload

```json
{
  "name": "Gateway of India",
  "street": "Apollo Bandar, Colaba",
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "400001",
  "latitude": 18.9220,
  "longitude": 72.8347
}
```

### Field Validations

| Field         | Rule                            |
|---------------|---------------------------------|
| `latitude`    | `-90.0` to `90.0`               |
| `longitude`   | `-180.0` to `180.0`             |
| All strings   | Non-empty, max length enforced  |
| Coordinates   | Unique — no two addresses can share the same lat/lon |

---

## List Addresses

```
GET /addresses/?search=mumbai&offset=0&limit=20
```

| Parameter | Default | Max   | Description                                  |
|-----------|---------|-------|----------------------------------------------|
| `search`  | —       | —     | Partial match on `name`, `city`, or `street` |
| `offset`  | `0`     | —     | Pagination offset (0-based)                  |
| `limit`   | `20`    | `500` | Page size                                    |

**Response:**
```json
{
  "data": {
    "total": 5,
    "offset": 0,
    "limit": 20,
    "items": [ ... ]
  },
  "message": "Addresses retrieved successfully.",
  "status": "success"
}
```

---

## Distance Search

```
GET /addresses/nearby?latitude=18.5195&longitude=73.8553&distance_km=100
```

Returns all addresses within `distance_km` kilometres of the given coordinates,
calculated using the [Haversine formula](https://en.wikipedia.org/wiki/Haversine_formula).

---

## Idempotency

To prevent duplicate submissions (network retries, double-clicks), send an `Idempotency-Key` header with `POST` / `PATCH` requests:

```bash
curl -X POST "http://localhost:8000/addresses/" \
     -H "X-API-Key: changeme-secret-key" \
     -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
     -H "Content-Type: application/json" \
     -d '{ "name": "Gateway of India", ... }'
```

- If the same key is sent again within **24 hours**, the original response is returned without re-processing
- Replayed responses include the header `X-Idempotency-Replayed: true`
- Error responses (`4xx` / `5xx`) are never cached — the client must use a new key to retry

---

## Standard Response Format

Every endpoint returns the same envelope:

**Success:**
```json
{
  "data": { ... },
  "message": "Address created successfully.",
  "status": "success"
}
```

**Error:**
```json
{
  "data": null,
  "message": "An address with these coordinates already exists.",
  "status": "error"
}
```

---

## Testing in Swagger

### Step 1 — Authenticate
1. Open `http://localhost:8000/docs`
2. Click the **Authorize** button (top right)
3. Enter `changeme-secret-key` → click **Authorize**

---

### Step 2 — Create an address (`POST /addresses/`)

```json
{
  "name": "Gateway of India",
  "street": "Apollo Bandar, Colaba",
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "400001",
  "latitude": 18.9220,
  "longitude": 72.8347
}
```

Copy the `id` (UUID) from the response — you'll need it for the next steps.

---

### Step 3 — Get the address (`GET /addresses/{id}`)

Paste the UUID from Step 2 into the `id` field.

---

### Step 4 — Update the address (`PATCH /addresses/{id}`)

Paste the UUID and send only the fields you want to change:

```json
{
  "city": "Navi Mumbai"
}
```

---

### Step 5 — List addresses (`GET /addresses/`)

| Parameter | Example value | Effect |
|---|---|---|
| `search` | `mumbai` | Filter by name / city / street |
| `offset` | `0` | Start from first record |
| `limit` | `10` | Return 10 records per page |

---

### Step 6 — Distance search (`GET /addresses/nearby`)

Find all addresses within 100 km of Pune:

| Parameter | Value |
|---|---|
| `latitude` | `18.5195` |
| `longitude` | `73.8553` |
| `distance_km` | `100` |

---

### Step 7 — Delete the address (`DELETE /addresses/{id}`)

Paste the UUID — returns `200` with `"status": "success"`.

---

### Step 8 — Test idempotency (`POST /addresses/`)

Add header `Idempotency-Key: test-key-12345` and submit the same body twice.  
Second response will include `X-Idempotency-Replayed: true` — no duplicate is created.

---

### Step 9 — Test validation errors

**Invalid latitude → 422:**
```json
{
  "name": "Test",
  "street": "Test Street",
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "400001",
  "latitude": 999,
  "longitude": 72.8347
}
```

**Duplicate coordinates → 409:** Submit the same body from Step 2 again.

---

## Project Structure

```
address-book/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, exception handlers
│   ├── config.py                # pydantic-settings config
│   ├── database.py              # Async SQLAlchemy engine + session dependency
│   ├── logging_config.py        # structlog setup
│   ├── dependencies/
│   │   └── auth.py              # API key authentication
│   ├── middleware/
│   │   └── idempotency.py       # Idempotency key middleware
│   ├── models/
│   │   └── address.py           # SQLAlchemy model
│   ├── schemas/
│   │   ├── address.py           # Pydantic request/response schemas
│   │   └── response.py          # Generic APIResponse[T] envelope
│   ├── routers/
│   │   └── address.py           # Route handlers
│   ├── services/
│   │   └── address.py           # Business logic
│   └── utils/
│       └── geo.py               # Haversine distance formula
├── tests/
│   ├── conftest.py              # Fixtures (in-memory DB, test client)
│   └── test_addresses.py        # 22 tests
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```
