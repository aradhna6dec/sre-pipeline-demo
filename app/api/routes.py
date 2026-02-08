"""
API Routes
Business logic endpoints with proper error handling
"""

import asyncio
import random
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request, status

from app.core.logging_config import get_logger
from app.core.metrics import metrics
from app.models.schemas import ErrorResponse, ItemCreate, ItemResponse

logger = get_logger(__name__)

api_router = APIRouter()


@api_router.get("/items", response_model=List[ItemResponse], tags=["items"])
async def get_items(
    skip: int = 0, limit: int = 10, request: Request = None
) -> List[ItemResponse]:
    """
    Get list of items (example endpoint)
    Demonstrates pagination and correlation ID usage
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.info(
        "Fetching items",
        extra={"correlation_id": correlation_id, "skip": skip, "limit": limit},
    )

    # Simulate database query
    await asyncio.sleep(0.01)

    items = [
        ItemResponse(
            id=i,
            name=f"Item {i}",
            description=f"Description for item {i}",
            price=round(random.uniform(10, 1000), 2),
            available=random.choice([True, False]),
        )
        for i in range(skip, skip + limit)
    ]

    metrics.items_processed_total.labels(operation="get_items", status="success").inc(
        len(items)
    )

    return items


@api_router.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
async def get_item(item_id: int, request: Request = None) -> ItemResponse:
    """
    Get a specific item by ID
    Demonstrates error handling
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.info(
        "Fetching item", extra={"correlation_id": correlation_id, "item_id": item_id}
    )

    # Simulate occasional errors for testing
    if item_id < 0:
        logger.warning(
            "Invalid item ID requested",
            extra={"correlation_id": correlation_id, "item_id": item_id},
        )
        metrics.errors_total.labels(
            error_type="validation_error", severity="warning"
        ).inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item ID must be non-negative",
        )

    if item_id == 999:
        logger.error(
            "Item not found",
            extra={"correlation_id": correlation_id, "item_id": item_id},
        )
        metrics.errors_total.labels(error_type="not_found", severity="info").inc()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Item {item_id} not found"
        )

    # Simulate database query
    await asyncio.sleep(0.01)

    item = ItemResponse(
        id=item_id,
        name=f"Item {item_id}",
        description=f"Description for item {item_id}",
        price=round(random.uniform(10, 1000), 2),
        available=True,
    )

    metrics.items_processed_total.labels(operation="get_item", status="success").inc()

    return item


@api_router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["items"],
)
async def create_item(item: ItemCreate, request: Request = None) -> ItemResponse:
    """
    Create a new item
    Demonstrates POST operations
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.info(
        "Creating item",
        extra={"correlation_id": correlation_id, "item_name": item.name},
    )

    # Simulate database insertion
    await asyncio.sleep(0.02)

    new_item = ItemResponse(
        id=random.randint(1000, 9999),
        name=item.name,
        description=item.description,
        price=item.price,
        available=True,
    )

    metrics.items_processed_total.labels(
        operation="create_item", status="success"
    ).inc()

    logger.info(
        "Item created", extra={"correlation_id": correlation_id, "item_id": new_item.id}
    )

    return new_item


@api_router.get("/slow", tags=["testing"])
async def slow_endpoint(delay: int = 5) -> Dict[str, Any]:
    """
    Intentionally slow endpoint for testing timeouts and monitoring
    """
    await asyncio.sleep(min(delay, 30))  # Max 30 seconds
    return {"message": f"Completed after {delay} seconds"}


@api_router.get("/error", tags=["testing"])
async def error_endpoint(error_type: str = "500") -> Dict[str, Any]:
    """
    Endpoint that returns different error types for testing error handling
    """
    error_map = {
        "400": (status.HTTP_400_BAD_REQUEST, "Bad Request"),
        "401": (status.HTTP_401_UNAUTHORIZED, "Unauthorized"),
        "403": (status.HTTP_403_FORBIDDEN, "Forbidden"),
        "404": (status.HTTP_404_NOT_FOUND, "Not Found"),
        "500": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error"),
        "503": (status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable"),
    }

    if error_type not in error_map:
        error_type = "500"

    status_code, detail = error_map[error_type]

    metrics.errors_total.labels(error_type=f"http_{error_type}", severity="error").inc()

    raise HTTPException(status_code=status_code, detail=detail)


@api_router.get("/cache-test", tags=["testing"])
async def cache_test(use_cache: bool = True) -> Dict[str, Any]:
    """
    Endpoint to test cache metrics
    """
    cache_name = "test_cache"

    if use_cache and random.random() > 0.5:
        # Cache hit
        metrics.cache_hits_total.labels(cache_name=cache_name).inc()
        return {"source": "cache", "data": "cached_data"}
    else:
        # Cache miss
        metrics.cache_misses_total.labels(cache_name=cache_name).inc()
        await asyncio.sleep(0.1)  # Simulate slow operation
        return {"source": "database", "data": "fresh_data"}
