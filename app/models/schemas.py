"""
Pydantic Models/Schemas
Data validation and serialization
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Base item schema"""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(
        None, max_length=500, description="Item description"
    )
    price: float = Field(..., gt=0, description="Item price (must be positive)")


class ItemCreate(ItemBase):
    """Schema for creating an item"""

    pass


class ItemResponse(ItemBase):
    """Schema for item response"""

    id: int = Field(..., description="Unique item identifier")
    available: bool = Field(default=True, description="Item availability")

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Schema for error responses"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class HealthResponse(BaseModel):
    """Schema for health check responses"""

    status: str = Field(..., description="Health status")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime")
