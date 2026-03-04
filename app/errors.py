from fastapi import HTTPException
from typing import Optional, Dict, Any


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code)
        self.error_code = error_code
        self.message = message
        self.details = details


# =====================================================
# Каталог ошибок
# =====================================================

def product_not_found(product_id: int):
    return AppException(
        status_code=404,
        error_code="PRODUCT_NOT_FOUND",
        message=f"Product with id={product_id} not found",
    )


def product_inactive():
    return AppException(
        status_code=409,
        error_code="PRODUCT_INACTIVE",
        message="Product is not active",
    )


def order_not_found(order_id: int):
    return AppException(
        status_code=404,
        error_code="ORDER_NOT_FOUND",
        message=f"Order with id={order_id} not found",
    )


def order_has_active():
    return AppException(
        status_code=409,
        error_code="ORDER_HAS_ACTIVE",
        message="User already has active order",
    )


def order_limit_exceeded():
    return AppException(
        status_code=429,
        error_code="ORDER_LIMIT_EXCEEDED",
        message="Order limit exceeded",
    )


def invalid_state_transition():
    return AppException(
        status_code=409,
        error_code="INVALID_STATE_TRANSITION",
        message="Cannot change order state",
    )


def insufficient_stock():
    return AppException(
        status_code=409,
        error_code="INSUFFICIENT_STOCK",
        message="Not enough stock",
    )


def validation_error(details):
    return AppException(
        status_code=400,
        error_code="VALIDATION_ERROR",
        message="Validation failed",
        details=details,
    )