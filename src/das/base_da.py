"""
Base Data Access Layer for CRUD operations.

KEY DESIGN DECISION:
- DA layer receives DICT of fields, not Pydantic schemas
- This creates clean separation: DA only knows about database operations
- Logic layer handles schema conversion
"""
import logging
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import BaseModel

logger = logging.getLogger(__name__)

# Generic type for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)


def get_utc_timestamp() -> int:
    """
    Get current UTC timestamp as integer (seconds since epoch).
    
    All timestamps in the system are stored as integers in UTC.
    This ensures:
    - Consistent timezone handling
    - Easy comparison and sorting
    - Compatibility across systems
    """
    return int(time.time())


class BaseDA:
    """
    Base Data Access class providing async CRUD operations.
    
    This class is designed to be inherited by specific entity DA classes.
    It provides common database operations that work with any model.
    
    Key Features:
    - All operations are async for FastAPI compatibility
    - Takes dict fields (not Pydantic schemas) for clean separation
    - Automatic UTC timestamp management
    - Soft deletes (status='deleted') to preserve data
    - Error handling and logging
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the DA with a specific model class.
        
        Args:
            model: SQLAlchemy model class (Template, MessageHistory, etc.)
        """
        self.model = model
        self.model_name = model.__name__
        logger.debug(f"Initialized {self.__class__.__name__} for {self.model_name}")
    
    async def insert(self, db: AsyncSession, fields: Dict[str, Any]) -> ModelType:
        """
        Insert a new record into the database.
        
        This method:
        1. Takes a dict of field→value pairs
        2. Adds UTC timestamps automatically
        3. Creates a model instance
        4. Inserts it into the database
        5. Returns the created model
        
        Args:
            db: Database session
            fields: Dictionary of field names and values
        
        Returns:
            Created model instance with generated id
        
        Raises:
            Exception: Database errors (unique constraint violations, etc.)
        """
        try:
            # Generate UUID in Python (avoids need for refresh!)
            from uuid import uuid4
            if 'id' not in fields:
                fields['id'] = uuid4()
            
            # Add UTC timestamps
            fields['creation_date'] = get_utc_timestamp()
            fields['update_date'] = get_utc_timestamp()
            
            # Set default status if not provided
            if 'status' not in fields:
                fields['status'] = 'active'
            
            # Create model instance from dict
            instance = self.model(**fields)
            
            # Add to session and flush (no refresh needed - we have the ID!)
            db.add(instance)
            await db.flush()
            
            logger.info(f"Inserted {self.model_name} with id={instance.id}")
            return instance
            
        except Exception as e:
            logger.error(f"Error inserting {self.model_name}: {e}")
            raise
    
    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: UUID of the record
            include_deleted: If True, include soft-deleted records
        
        Returns:
            Model instance or None if not found
        """
        try:
            stmt = select(self.model).where(self.model.id == id)
            
            # Exclude deleted records by default
            if not include_deleted:
                stmt = stmt.where(self.model.status != 'deleted')
            
            result = await db.execute(stmt)
            instance = result.scalar_one_or_none()
            
            if instance:
                logger.debug(f"Found {self.model_name} with id={id}")
            else:
                logger.debug(f"{self.model_name} with id={id} not found")
            
            return instance
            
        except Exception as e:
            logger.error(f"Error getting {self.model_name} by id={id}: {e}")
            raise
    
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            include_deleted: If True, include soft-deleted records
        
        Returns:
            List of model instances
        """
        try:
            stmt = select(self.model)
            
            # Exclude deleted records by default
            if not include_deleted:
                stmt = stmt.where(self.model.status != 'deleted')
            
            # Add pagination
            stmt = stmt.offset(skip).limit(limit)
            
            result = await db.execute(stmt)
            instances = result.scalars().all()
            
            logger.debug(f"Found {len(instances)} {self.model_name} records")
            return list(instances)
            
        except Exception as e:
            logger.error(f"Error getting all {self.model_name}: {e}")
            raise
    
    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        fields: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        IMPORTANT: Cannot update deleted records or change status from 'deleted' to anything else.
        Once deleted (soft delete), a record cannot be "undeleted" via API.
        
        Args:
            db: Database session
            id: UUID of the record to update
            fields: Dictionary of fields to update
        
        Returns:
            Updated model instance or None if not found
        
        Raises:
            ValueError: If trying to update a deleted record
        """
        try:
            # Check if record exists and is not deleted
            existing = await self.get_by_id(db, id, include_deleted=False)
            if not existing:
                logger.warning(f"{self.model_name} with id={id} not found for update")
                return None
            
            # BLOCK: Cannot change status from 'deleted' back to 'active'
            # This check is redundant since get_by_id excludes deleted, but explicit is better
            if existing.status == 'deleted':
                logger.error(f"Cannot update deleted {self.model_name} with id={id}")
                raise ValueError(f"Cannot update deleted {self.model_name}")
            
            # BLOCK: Cannot manually set status to 'deleted' via update
            # Use delete() method instead
            if 'status' in fields and fields['status'] == 'deleted':
                logger.error(f"Cannot manually set status to 'deleted'. Use delete() method instead.")
                raise ValueError("Use delete() method to delete records, not update()")
            
            # Update timestamp
            fields['update_date'] = get_utc_timestamp()
            
            # Perform update
            stmt = (
                sql_update(self.model)
                .where(self.model.id == id)
                .values(**fields)
            )
            await db.execute(stmt)
            await db.flush()
            
            # Fetch updated record
            updated = await self.get_by_id(db, id, include_deleted=False)
            
            logger.info(f"Updated {self.model_name} with id={id}")
            return updated
            
        except Exception as e:
            logger.error(f"Error updating {self.model_name} with id={id}: {e}")
            raise
    
    async def delete(
        self,
        db: AsyncSession,
        id: UUID
    ) -> bool:
        """
        Delete a record (soft delete ONLY).
        
        IMPORTANT: This only performs soft delete (sets status='deleted').
        We NEVER physically delete data from the database.
        
        This preserves:
        - Audit trails
        - Data history
        - Referential integrity
        - Ability to recover deleted items
        
        Args:
            db: Database session
            id: UUID of the record to delete
        
        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if record exists
            existing = await self.get_by_id(db, id, include_deleted=False)
            if not existing:
                logger.warning(f"{self.model_name} with id={id} not found for delete")
                return False
            
            # Soft delete ONLY: set status to 'deleted'
            # We update directly to avoid the check in update() method
            fields = {
                'status': 'deleted',
                'update_date': get_utc_timestamp()
            }
            stmt = (
                sql_update(self.model)
                .where(self.model.id == id)
                .values(**fields)
            )
            await db.execute(stmt)
            await db.flush()
            
            logger.info(f"Soft deleted {self.model_name} with id={id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {self.model_name} with id={id}: {e}")
            raise
