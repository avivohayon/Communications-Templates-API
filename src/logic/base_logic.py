"""
Base Business Logic Layer.

KEY RESPONSIBILITY:
- Logic layer receives Pydantic schemas from API layer
- Converts schemas to dicts before calling DA layer
- Handles business rules and validation
- Converts models back to schemas for API responses
"""
import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel as PydanticBaseModel

from src.das.base_da import BaseDA
from src.schemas.base_schema import AppBaseSchema, AppSchemaOut

logger = logging.getLogger(__name__)

# Generic types
SchemaInType = TypeVar('SchemaInType', bound=AppBaseSchema)
SchemaOutType = TypeVar('SchemaOutType', bound=AppSchemaOut)
SchemaUpdateType = TypeVar('SchemaUpdateType', bound=AppBaseSchema)


class BaseLogic(Generic[SchemaInType, SchemaOutType, SchemaUpdateType]):
    """
    Base Business Logic class providing common operations.
    
    This class handles:
    - Schema to dict conversion for DA layer
    - Model to schema conversion for API responses
    - Common business rules
    - Error handling and logging
    
    Design Pattern:
    API Layer (FastAPI) → Pydantic Schema → Logic Layer → Dict → DA Layer → Database
    Database → Model → DA Layer → Logic Layer → Pydantic Schema → API Layer
    """
    
    def __init__(
        self,
        da: BaseDA,
        schema_out_class: type[SchemaOutType]
    ):
        """
        Initialize the logic layer with a DA instance and output schema class.
        
        Args:
            da: Data Access instance (TemplateDA, etc.)
            schema_out_class: Pydantic output schema class for responses
        """
        self.da = da
        self.schema_out_class = schema_out_class
        self.entity_name = da.model_name
        logger.debug(f"Initialized {self.__class__.__name__} for {self.entity_name}")
    
    async def create(
        self,
        db: AsyncSession,
        schema: SchemaInType
    ) -> SchemaOutType:
        """
        Create a new entity.
        
        Flow:
        1. Receive Pydantic schema from API
        2. Convert schema to dict using model_dump()
        3. Pass dict to DA layer for insertion
        4. Convert returned model back to schema
        5. Return schema to API
        
        Args:
            db: Database session
            schema: Input schema with data to create
        
        Returns:
            Output schema with created entity (includes id, timestamps)
        
        Raises:
            Exception: Business rule violations, database errors
        """
        try:
            # Convert Pydantic schema to dict
            fields = schema.model_dump()
            
            logger.info(f"Creating {self.entity_name}")
            
            # Call DA layer with dict
            model = await self.da.insert(db, fields)
            
            # Convert model back to Pydantic schema
            result = self.schema_out_class.model_validate(model)
            
            logger.info(f"Created {self.entity_name} with id={result.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating {self.entity_name}: {e}")
            raise
    
    async def get_by_id(
        self,
        db: AsyncSession,
        id: UUID
    ) -> Optional[SchemaOutType]:
        """
        Get an entity by ID.
        
        Args:
            db: Database session
            id: UUID of the entity
        
        Returns:
            Output schema or None if not found
        """
        try:
            model = await self.da.get_by_id(db, id)
            
            if not model:
                logger.debug(f"{self.entity_name} with id={id} not found")
                return None
            
            # Convert model to schema
            result = self.schema_out_class.model_validate(model)
            return result
            
        except Exception as e:
            logger.error(f"Error getting {self.entity_name} by id={id}: {e}")
            raise
    
    async def get_all(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[SchemaOutType]:
        """
        Get all entities with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of output schemas
        """
        try:
            models = await self.da.get_all(db, skip=skip, limit=limit)
            
            # Convert all models to schemas
            results = [
                self.schema_out_class.model_validate(model)
                for model in models
            ]
            
            logger.debug(f"Retrieved {len(results)} {self.entity_name} records")
            return results
            
        except Exception as e:
            logger.error(f"Error getting all {self.entity_name}: {e}")
            raise
    
    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        schema: SchemaUpdateType
    ) -> Optional[SchemaOutType]:
        """
        Update an existing entity.
        
        Args:
            db: Database session
            id: UUID of the entity to update
            schema: Update schema with fields to change
        
        Returns:
            Updated output schema or None if not found
        """
        try:
            # Convert schema to dict, excluding unset fields
            fields = schema.model_dump(exclude_unset=True)
            
            if not fields:
                logger.warning(f"No fields provided for {self.entity_name} update")
                return await self.get_by_id(db, id)
            
            logger.info(f"Updating {self.entity_name} with id={id}")
            
            # Call DA layer with dict
            model = await self.da.update(db, id, fields)
            
            if not model:
                logger.warning(f"{self.entity_name} with id={id} not found for update")
                return None
            
            # Convert model to schema
            result = self.schema_out_class.model_validate(model)
            
            logger.info(f"Updated {self.entity_name} with id={id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating {self.entity_name} with id={id}: {e}")
            raise
    
    async def delete(
        self,
        db: AsyncSession,
        id: UUID
    ) -> bool:
        """
        Delete an entity (soft delete by default).
        
        Args:
            db: Database session
            id: UUID of the entity to delete
        
        Returns:
            True if deleted, False if not found
        """
        try:
            logger.info(f"Deleting {self.entity_name} with id={id}")
            
            result = await self.da.delete(db, id)
            
            if result:
                logger.info(f"Deleted {self.entity_name} with id={id}")
            else:
                logger.warning(f"{self.entity_name} with id={id} not found for delete")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting {self.entity_name} with id={id}: {e}")
            raise
