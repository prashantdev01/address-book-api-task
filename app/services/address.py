import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate
from app.utils.geo import haversine_distance

logger = structlog.get_logger(__name__)


class AddressService:
    """Encapsulates all business logic for address operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: AddressCreate) -> Address:
        address = Address(**data.model_dump())
        try:
            self.db.add(address)
            await self.db.commit()
            await self.db.refresh(address)
        except IntegrityError:
            await self.db.rollback()
            logger.warning("address_duplicate_coordinates", lat=data.latitude, lon=data.longitude)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An address with these coordinates already exists.",
            )
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error("address_create_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create address.",
            )
        logger.info("address_created", address_id=str(address.id), name=address.name)
        return address

    async def get_by_id(self, address_id: uuid.UUID) -> Address:
        try:
            result = await self.db.execute(select(Address).where(Address.id == address_id))
        except SQLAlchemyError as e:
            logger.error("address_fetch_failed", address_id=str(address_id), error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch address.",
            )
        address = result.scalar_one_or_none()
        if address is None:
            logger.warning("address_not_found", address_id=str(address_id))
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address with id {address_id} not found.",
            )
        return address

    async def list_all(
        self,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[int, list[Address]]:
        try:
            query = select(Address)
            if search:
                pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Address.name.ilike(pattern),
                        Address.city.ilike(pattern),
                        Address.street.ilike(pattern),
                    )
                )
            total_result = await self.db.execute(
                select(func.count()).select_from(query.subquery())
            )
            total = total_result.scalar_one()
            result = await self.db.execute(
                query.order_by(Address.created_at).offset(offset).limit(limit)
            )
            return total, list(result.scalars().all())
        except SQLAlchemyError as e:
            logger.error("address_list_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch addresses.",
            )

    async def update(self, address_id: uuid.UUID, data: AddressUpdate) -> Address:
        address = await self.get_by_id(address_id)
        update_data = data.model_dump(exclude_unset=True)
        try:
            for field, value in update_data.items():
                setattr(address, field, value)
            await self.db.commit()
            await self.db.refresh(address)
        except IntegrityError:
            await self.db.rollback()
            logger.warning("address_update_duplicate_coordinates", address_id=str(address_id))
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An address with these coordinates already exists.",
            )
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error("address_update_failed", address_id=str(address_id), error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update address.",
            )
        logger.info("address_updated", address_id=str(address_id), updated_fields=list(update_data.keys()))
        return address

    async def delete(self, address_id: uuid.UUID) -> None:
        address = await self.get_by_id(address_id)
        try:
            await self.db.delete(address)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error("address_delete_failed", address_id=str(address_id), error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete address.",
            )
        logger.info("address_deleted", address_id=str(address_id))

    async def find_nearby(
        self, latitude: float, longitude: float, distance_km: float
    ) -> list[Address]:
        _, all_addresses = await self.list_all(offset=0, limit=10_000)
        nearby = [
            addr
            for addr in all_addresses
            if haversine_distance(latitude, longitude, addr.latitude, addr.longitude) <= distance_km
        ]
        logger.info(
            "nearby_search_completed",
            origin_lat=latitude,
            origin_lon=longitude,
            radius_km=distance_km,
            results_found=len(nearby),
        )
        return nearby
