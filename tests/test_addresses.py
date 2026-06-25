import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SHANIWAR_WADA = {
    "name": "Shaniwar Wada",
    "street": "Shivajinagar",
    "city": "Pune",
    "state": "Maharashtra",
    "country": "India",
    "postal_code": "411005",
    "latitude": 18.5195,
    "longitude": 73.8553,
}


VIDHANA_SOUDHA = {
    "name": "Vidhana Soudha",
    "street": "Dr. Ambedkar Veedhi",
    "city": "Bangalore",
    "state": "Karnataka",
    "country": "India",
    "postal_code": "560001",
    "latitude": 12.9793,
    "longitude": 77.5906,
}

LALBAGH_GARDEN = {
    "name": "Lalbagh Botanical Garden",
    "street": "Mavalli, Lalbagh Road",
    "city": "Bangalore",
    "state": "Karnataka",
    "country": "India",
    "postal_code": "560004",
    "latitude": 12.9507,
    "longitude": 77.5848,
}

NONEXISTENT_ID = str(uuid.uuid4())


def assert_success(body: dict) -> dict:
    assert body["status"] == "success"
    assert body["data"] is not None
    return body["data"]


def assert_error(body: dict) -> None:
    assert body["status"] == "error"
    assert body["data"] is None
    assert "message" in body


# --- CRUD ---

async def test_create_address_returns_201(client: AsyncClient) -> None:
    response = await client.post("/addresses/", json=SHANIWAR_WADA)
    assert response.status_code == 201
    data = assert_success(response.json())
    assert data["name"] == SHANIWAR_WADA["name"]
    assert data["latitude"] == SHANIWAR_WADA["latitude"]
    assert uuid.UUID(data["id"])
    assert "created_at" in data


async def test_get_address_by_id(client: AsyncClient) -> None:
    created = assert_success((await client.post("/addresses/", json=SHANIWAR_WADA)).json())
    response = await client.get(f"/addresses/{created['id']}")
    assert response.status_code == 200
    data = assert_success(response.json())
    assert data["id"] == created["id"]


async def test_get_address_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get(f"/addresses/{NONEXISTENT_ID}")
    assert response.status_code == 404
    assert_error(response.json())


async def test_list_addresses(client: AsyncClient) -> None:
    await client.post("/addresses/", json=SHANIWAR_WADA)
    await client.post("/addresses/", json=VIDHANA_SOUDHA)
    response = await client.get("/addresses/")
    assert response.status_code == 200
    data = assert_success(response.json())
    assert data["total"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2


async def test_list_addresses_pagination(client: AsyncClient) -> None:
    await client.post("/addresses/", json=SHANIWAR_WADA)
    await client.post("/addresses/", json=VIDHANA_SOUDHA)
    response = await client.get("/addresses/", params={"offset": 1, "limit": 1})
    assert response.status_code == 200
    data = assert_success(response.json())
    assert data["total"] == 2
    assert len(data["items"]) == 1


async def test_list_addresses_search(client: AsyncClient) -> None:
    await client.post("/addresses/", json=SHANIWAR_WADA)
    await client.post("/addresses/", json=VIDHANA_SOUDHA)
    response = await client.get("/addresses/", params={"search": "pune"})
    assert response.status_code == 200
    data = assert_success(response.json())
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Shaniwar Wada"


async def test_update_address_partial(client: AsyncClient) -> None:
    created = assert_success((await client.post("/addresses/", json=SHANIWAR_WADA)).json())
    response = await client.patch(f"/addresses/{created['id']}", json={"city": "Mumbai"})
    assert response.status_code == 200
    data = assert_success(response.json())
    assert data["city"] == "Mumbai"
    assert data["name"] == SHANIWAR_WADA["name"]


async def test_update_nonexistent_address_returns_404(client: AsyncClient) -> None:
    response = await client.patch(f"/addresses/{NONEXISTENT_ID}", json={"city": "Mumbai"})
    assert response.status_code == 404
    assert_error(response.json())


async def test_delete_address(client: AsyncClient) -> None:
    created = assert_success((await client.post("/addresses/", json=SHANIWAR_WADA)).json())
    delete_resp = await client.delete(f"/addresses/{created['id']}")
    assert delete_resp.status_code == 200
    body = delete_resp.json()
    assert body["status"] == "success"
    assert body["data"] is None
    get_resp = await client.get(f"/addresses/{created['id']}")
    assert get_resp.status_code == 404


async def test_delete_nonexistent_address_returns_404(client: AsyncClient) -> None:
    response = await client.delete(f"/addresses/{NONEXISTENT_ID}")
    assert response.status_code == 404
    assert_error(response.json())


async def test_duplicate_coordinates_returns_409(client: AsyncClient) -> None:
    await client.post("/addresses/", json=SHANIWAR_WADA)
    response = await client.post("/addresses/", json=SHANIWAR_WADA)
    assert response.status_code == 409
    assert_error(response.json())


# --- Validation ---

async def test_invalid_latitude_returns_422(client: AsyncClient) -> None:
    payload = {**SHANIWAR_WADA, "latitude": 200.0}
    response = await client.post("/addresses/", json=payload)
    assert response.status_code == 422
    assert_error(response.json())


async def test_invalid_longitude_returns_422(client: AsyncClient) -> None:
    payload = {**SHANIWAR_WADA, "longitude": -200.0}
    response = await client.post("/addresses/", json=payload)
    assert response.status_code == 422
    assert_error(response.json())


async def test_missing_required_field_returns_422(client: AsyncClient) -> None:
    payload = {k: v for k, v in SHANIWAR_WADA.items() if k != "city"}
    response = await client.post("/addresses/", json=payload)
    assert response.status_code == 422
    assert_error(response.json())


# --- Nearby Search ---

async def test_nearby_returns_only_close_addresses(client: AsyncClient) -> None:
    await client.post("/addresses/", json=SHANIWAR_WADA)
    await client.post("/addresses/", json=VIDHANA_SOUDHA)
    response = await client.get(
        "/addresses/nearby",
        params={"latitude": 18.520, "longitude": 73.860, "distance_km": 5},
    )
    assert response.status_code == 200
    data = assert_success(response.json())
    assert len(data) == 1
    assert data[0]["name"] == "Shaniwar Wada"


async def test_nearby_returns_all_within_radius(client: AsyncClient) -> None:
    await client.post("/addresses/", json=SHANIWAR_WADA)
    await client.post("/addresses/", json=VIDHANA_SOUDHA)
    response = await client.get(
        "/addresses/nearby",
        params={"latitude": 18.520, "longitude": 73.860, "distance_km": 1000},
    )
    assert response.status_code == 200
    data = assert_success(response.json())
    assert len(data) == 2


async def test_nearby_returns_both_bangalore_addresses(client: AsyncClient) -> None:
    await client.post("/addresses/", json=VIDHANA_SOUDHA)
    await client.post("/addresses/", json=LALBAGH_GARDEN)
    await client.post("/addresses/", json=SHANIWAR_WADA)
    # 10 km from Bangalore city centre — should return both Bangalore addresses, not Pune
    response = await client.get(
        "/addresses/nearby",
        params={"latitude": 12.9716, "longitude": 77.5946, "distance_km": 10},
    )
    assert response.status_code == 200
    data = assert_success(response.json())
    assert len(data) == 2
    names = {item["name"] for item in data}
    assert names == {"Vidhana Soudha", "Lalbagh Botanical Garden"}


async def test_nearby_invalid_params_returns_422(client: AsyncClient) -> None:
    response = await client.get(
        "/addresses/nearby",
        params={"latitude": 48.860, "longitude": 2.300, "distance_km": -1},
    )
    assert response.status_code == 422
    assert_error(response.json())


# --- Idempotency ---

async def test_idempotency_key_prevents_duplicate_create(client: AsyncClient) -> None:
    key = str(uuid.uuid4())
    headers = {"Idempotency-Key": key}

    r1 = await client.post("/addresses/", json=SHANIWAR_WADA, headers=headers)
    assert r1.status_code == 201

    # Second call with the same key — must NOT create a duplicate
    r2 = await client.post("/addresses/", json=SHANIWAR_WADA, headers=headers)
    assert r2.status_code == 201
    assert r2.headers.get("X-Idempotency-Replayed") == "true"
    assert r1.json()["data"]["id"] == r2.json()["data"]["id"]

    # Confirm only one record exists
    list_resp = await client.get("/addresses/")
    assert list_resp.json()["data"]["total"] == 1


async def test_different_idempotency_keys_create_separate_records(client: AsyncClient) -> None:
    r1 = await client.post(
        "/addresses/", json=SHANIWAR_WADA, headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert r1.status_code == 201

    # Different address + different key → should succeed
    r2 = await client.post(
        "/addresses/", json=VIDHANA_SOUDHA, headers={"Idempotency-Key": str(uuid.uuid4())}
    )
    assert r2.status_code == 201
    assert r1.json()["data"]["id"] != r2.json()["data"]["id"]


# --- Authentication ---

async def test_missing_api_key_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/addresses/", json=SHANIWAR_WADA, headers={"X-API-Key": ""}
    )
    assert response.status_code == 401
    assert_error(response.json())


async def test_invalid_api_key_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/addresses/", json=SHANIWAR_WADA, headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401
    assert_error(response.json())


# --- Health ---

async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["version"] is not None
