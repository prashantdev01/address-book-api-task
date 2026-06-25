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
| `API_KEY`              | `prashant`                                 | API key for `X-API-Key` header     |
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

**Default API Key: `prashant`**

**In Swagger UI:**
1. Open `http://localhost:8000/docs`
2. Click the **Authorize** button (lock icon, top right)
3. Enter `prashant` in the `X-API-Key` field
4. Click **Authorize** → **Close**
5. All requests now include the key automatically

**In curl:**
```bash
curl -X GET "http://localhost:8000/addresses/" \
     -H "X-API-Key: prashant"
```

> Override in `.env`: `API_KEY=your-secret-key-here`

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

## Testing in Swagger — Step by Step

### Step 1 — Authorize

1. Open **http://localhost:8000/docs**
2. Click **Authorize** (lock icon, top right)
3. Enter `prashant` → click **Authorize** → **Close**

---

### Step 2 — Create an address (`POST /addresses/`)

Click `POST /addresses/` → **Try it out** → paste the body below → **Execute**

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

### Step 3 — Add more Maharashtra addresses

Use `POST /addresses/` with each payload below to populate the database for list and nearby tests.

**Shaniwar Wada, Pune**
```json
{
  "name": "Shaniwar Wada",
  "street": "Shivajinagar",
  "city": "Pune",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "411005",
  "latitude": 18.5195,
  "longitude": 73.8553
}
```

**Shirdi Sai Baba Temple**
```json
{
  "name": "Shirdi Sai Baba Temple",
  "street": "Shirdi Gram Panchayat Road",
  "city": "Shirdi",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "423109",
  "latitude": 19.7660,
  "longitude": 74.4771
}
```

**Ajanta Caves, Aurangabad**
```json
{
  "name": "Ajanta Caves",
  "street": "Ajanta Village, Sillod",
  "city": "Aurangabad",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "431117",
  "latitude": 20.5519,
  "longitude": 75.7033
}
```

**Trimbakeshwar Shiva Temple, Nashik**
```json
{
  "name": "Trimbakeshwar Shiva Temple",
  "street": "Trimbak Road",
  "city": "Nashik",
  "state": "Maharashtra",
  "country": "India",
  "postal_code": "422212",
  "latitude": 19.9323,
  "longitude": 73.5298
}
```

---

### Step 4 — List addresses (`GET /addresses/`)

Click `GET /addresses/` → **Try it out** → leave defaults → **Execute**

**With search filter:**

| Parameter | Value    | Effect                        |
|-----------|----------|-------------------------------|
| `search`  | `mumbai` | Returns only Mumbai addresses |
| `offset`  | `0`      | Start from first record       |
| `limit`   | `10`     | Return 10 per page            |

**Response:**
```json
{
  "data": {
    "total": 5,
    "offset": 0,
    "limit": 10,
    "items": [ ... ]
  },
  "message": "Addresses retrieved successfully.",
  "status": "success"
}
```

---

### Step 5 — Get address by ID (`GET /addresses/{id}`)

Click `GET /addresses/{id}` → **Try it out** → paste the UUID from Step 2 → **Execute**

---

### Step 6 — Update address (`PATCH /addresses/{id}`)

Click `PATCH /addresses/{id}` → **Try it out** → paste the UUID → send only the fields to change:

```json
{
  "city": "Navi Mumbai"
}
```

---

### Step 7 — Distance search (`GET /addresses/nearby`)

Find all addresses within 200 km of Pune:

| Parameter      | Value     |
|----------------|-----------|
| `latitude`     | `18.5195` |
| `longitude`    | `73.8553` |
| `distance_km`  | `200`     |

This will return Mumbai, Pune, Nashik, and Shirdi (all within 200 km of Pune).

---

### Step 8 — Delete address (`DELETE /addresses/{id}`)

Click `DELETE /addresses/{id}` → **Try it out** → paste the UUID → **Execute**

Returns `200` with `"status": "success"`.

---

### Step 9 — Test idempotency (`POST /addresses/`)

1. Click `POST /addresses/` → **Try it out**
2. Add header: `Idempotency-Key: test-key-12345`
3. Submit the Gateway of India body
4. Submit the **exact same body again** with the **same key**
5. Second response will include `X-Idempotency-Replayed: true` — no duplicate is created

---

### Step 10 — Test validation errors

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

**Duplicate coordinates → 409:** Submit the Gateway of India body twice without an idempotency key.

**Missing API key → 401:** Remove the `X-API-Key` header and try any request.

---

## Standard Response Format

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

## Field Validations

| Field         | Rule                                                         |
|---------------|--------------------------------------------------------------|
| `latitude`    | `-90.0` to `90.0`                                            |
| `longitude`   | `-180.0` to `180.0`                                          |
| All strings   | Non-empty, max length enforced                               |
| Coordinates   | Unique — no two addresses can share the same lat/lon         |

---

## Idempotency

To prevent duplicate submissions (network retries, double-clicks), send an `Idempotency-Key` header with `POST` / `PATCH` requests:

```bash
curl -X POST "http://localhost:8000/addresses/" \
     -H "X-API-Key: prashant" \
     -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
     -H "Content-Type: application/json" \
     -d '{ "name": "Gateway of India", ... }'
```

- Same key within **24 hours** → original response returned, no re-processing
- Replayed responses include `X-Idempotency-Replayed: true`
- Error responses (`4xx` / `5xx`) are never cached

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
