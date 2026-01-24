from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AppBaseSchema(BaseModel):
    """
    Base schema with common configuration for all Pydantic models.
    
    ConfigDict(from_attributes=True):
    - Allows creating Pydantic models from SQLAlchemy ORM objects
    - Enables use of model_validate(sqlalchemy_obj)
    - Modern Pydantic v2 approach (replaces orm_mode=True from v1)
    
    Usage:
    ```python
    template_model = await db.get(Template, template_id)  # SQLAlchemy model
    template_schema = TemplateOut.model_validate(template_model)  # Converts to Pydantic
    ```
    """
    model_config = ConfigDict(from_attributes=True)


class AppSchemaIn(AppBaseSchema):
    """
    Base schema for input/creation requests.
    
    Purpose: Used for POST endpoints
    Does NOT include: id, creation_date, update_date, status (auto-generated)
    """
    pass


class AppSchemaOut(AppBaseSchema):
    """
    Base schema for output/response data.
    
    Purpose: Used for GET endpoints and successful POST/PUT responses
    Includes: All fields that are returned to the client
    - id: Generated UUID
    - creation_date: UTC timestamp (integer)
    - update_date: UTC timestamp (integer)
    - status: Entity status ('active' or 'deleted')
    """
    id: UUID
    creation_date: int
    update_date: int
    status: str


class AppSchemaUpdate(AppBaseSchema):
    """
    Base schema for update/PUT requests.
    
    Purpose: Used for PUT endpoints
    All fields are optional to allow partial updates.
    """
    pass
