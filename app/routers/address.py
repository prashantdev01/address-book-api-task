import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import verify_api_key
from app.schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    PaginatedAddressResponse,
)
from app.schemas.response import APIResponse
from app.services.address import AddressService

router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"],
    dependencies=[Depends(verify_api_key)],
)


def get_address_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AddressService:
    return AddressService(db)


@router.post(
    "/",
    response_model=APIResponse[AddressResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new address",
)
async def create_address(
    payload: AddressCreate,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> APIResponse[AddressResponse]:
    """Create a new address with validated coordinates."""
    address = await service.create(payload)
    return APIResponse.success(data=address, message="Address created successfully.")


@router.get(
    "/nearby",
    response_model=APIResponse[list[AddressResponse]],
    summary="Find addresses within a distance",
)
async def get_nearby_addresses(
    latitude: Annotated[float, Query(ge=-90.0, le=90.0, description="Origin latitude", examples=[18.5195, 19.9323])],
    longitude: Annotated[float, Query(ge=-180.0, le=180.0, description="Origin longitude", examples=[73.8553, 73.5298])],
    distance_km: Annotated[float, Query(gt=0, description="Search radius in kilometers", examples=[50, 100, 250, 500])],
    service: Annotated[AddressService, Depends(get_address_service)],
) -> APIResponse[list[AddressResponse]]:
    """
    Return all addresses within `distance_km` kilometres of the provided origin,
    calculated using the Haversine formula.
    """
    addresses = await service.find_nearby(latitude, longitude, distance_km)
    return APIResponse.success(data=addresses, message=f"{len(addresses)} address(es) found.")


@router.get(
    "/",
    response_model=APIResponse[PaginatedAddressResponse],
    summary="List all addresses",
)
async def list_addresses(
    service: Annotated[AddressService, Depends(get_address_service)],
    search: Annotated[
        str | None, Query(description="Filter by name, city or street (partial match)")
    ] = None,
    offset: Annotated[int, Query(ge=0, description="Pagination offset (0-based)")] = 0,
    limit: Annotated[
        int,
        Query(ge=1, le=settings.pagination_max_limit, description=f"Page size (default 20, max {settings.pagination_max_limit})"),
    ] = 20,
) -> APIResponse[PaginatedAddressResponse]:
    """List addresses with optional search filter and pagination."""
    total, items = await service.list_all(offset=offset, limit=limit, search=search)
    return APIResponse.success(
        data=PaginatedAddressResponse(total=total, offset=offset, limit=limit, items=items),
        message="Addresses retrieved successfully.",
    )


@router.get(
    "/{address_id}",
    response_model=APIResponse[AddressResponse],
    summary="Get an address by ID",
)
async def get_address(
    address_id: uuid.UUID,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> APIResponse[AddressResponse]:
    """Retrieve a single address by its UUID."""
    address = await service.get_by_id(address_id)
    return APIResponse.success(data=address, message="Address retrieved successfully.")


@router.patch(
    "/{address_id}",
    response_model=APIResponse[AddressResponse],
    summary="Partially update an address",
)
async def update_address(
    address_id: uuid.UUID,
    payload: AddressUpdate,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> APIResponse[AddressResponse]:
    """Update only the provided fields of an existing address."""
    address = await service.update(address_id, payload)
    return APIResponse.success(data=address, message="Address updated successfully.")


@router.delete(
    "/{address_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete an address",
)
async def delete_address(
    address_id: uuid.UUID,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> APIResponse[None]:
    """Permanently delete an address by its UUID."""
    await service.delete(address_id)
    return APIResponse.success(data=None, message="Address deleted successfully.")
