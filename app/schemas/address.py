import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Label or name for this address")
    street: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to 90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to 180)")


class AddressCreate(AddressBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Gateway of India",
                    "street": "Apollo Bandar, Colaba",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "400001",
                    "latitude": 18.9220,
                    "longitude": 72.8347,
                },
                {
                    "name": "Shaniwar Wada",
                    "street": "Shivajinagar",
                    "city": "Pune",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "411005",
                    "latitude": 18.5195,
                    "longitude": 73.8553,
                },
                {
                    "name": "Shirdi Sai Baba Temple",
                    "street": "Shirdi Gram Panchayat Road",
                    "city": "Shirdi",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "423109",
                    "latitude": 19.7660,
                    "longitude": 74.4771,
                },
                {
                    "name": "Ajanta Caves",
                    "street": "Ajanta Village, Sillod",
                    "city": "Aurangabad",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "431117",
                    "latitude": 20.5519,
                    "longitude": 75.7033,
                },
                {
                    "name": "Trimbakeshwar Shiva Temple",
                    "street": "Trimbak Road",
                    "city": "Nashik",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "422212",
                    "latitude": 19.9323,
                    "longitude": 73.5298,
                },
            ]
        }
    )

    @field_validator("name", "street", "city", "state", "country", "postal_code", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class AddressUpdate(BaseModel):
    """All fields are optional; only provided fields are updated (PATCH semantics)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"city": "Nashik"},
                {"latitude": 19.9323, "longitude": 73.5298},
                {"name": "Updated Name", "street": "New Street", "postal_code": "400001"},
            ]
        }
    )

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    street: Optional[str] = Field(None, min_length=1, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=1, max_length=20)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)

    @field_validator("name", "street", "city", "state", "country", "postal_code", mode="before")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            return v.strip()
        return v


class AddressResponse(AddressBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAddressResponse(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[AddressResponse]
