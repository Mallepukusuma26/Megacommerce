"""
MegaCommerce Base Repository Abstraction
SQLAlchemy 2.0 Transaction-Safe CRUD Pattern
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete
from database.connection import Base
from shared.exceptions import ResourceNotFoundError

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository encapsulating data access & persistence logic for model entity T."""

    def __init__(self, model: Type[T], session: Session):
        self.model = model
        self.session = session

    def get_by_id(self, id_val: Any) -> Optional[T]:
        """Fetch entity by primary key."""
        stmt = select(self.model).where(self.model.id == str(id_val))
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id_or_raise(self, id_val: Any) -> T:
        """Fetch entity by primary key or raise ResourceNotFoundError."""
        entity = self.get_by_id(id_val)
        if not entity:
            raise ResourceNotFoundError(self.model.__name__, id_val)
        return entity

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve paginated records."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def count(self) -> int:
        """Get total record count."""
        stmt = select(func.count(self.model.id))
        return self.session.execute(stmt).scalar_one()

    def create(self, **kwargs) -> T:
        """Instantiate and persist a new model entity."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance

    def update(self, id_val: Any, **kwargs) -> T:
        """Update existing entity attributes."""
        instance = self.get_by_id_or_raise(id_val)
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        self.session.flush()
        return instance

    def delete(self, id_val: Any) -> bool:
        """Delete entity by primary key."""
        instance = self.get_by_id_or_raise(id_val)
        self.session.delete(instance)
        self.session.flush()
        return True
