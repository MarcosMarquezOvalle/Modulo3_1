"""
Layer 3 – Interface Adapters: CreateOrder Controller
====================================================
Translates a raw incoming payload (dict from HTTP, CLI args, test fixture…)
into the use-case request model, then delegates to the interactor.

The controller owns NO business logic. It validates data shape/types and
converts them — nothing more. Any semantic rule ("quantity must be > 0")
belongs in the entity.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

from src.use_cases.create_order.interactor import CreateOrderInteractor
from src.use_cases.create_order.request_model import CreateOrderRequest, OrderItemRequest


class CreateOrderController:
    """
    Framework-agnostic controller.  Accepts a raw dict so it can be driven
    by Flask, FastAPI, Django, CLI, or a test without any import changes.
    """

    def __init__(self, interactor: CreateOrderInteractor) -> None:
        self._interactor = interactor

    def handle(self, raw: Dict[str, Any]) -> None:
        """
        Parse *raw* (e.g. ``request.json`` from Flask) and invoke the use case.
        Raises ``ControllerValidationError`` for malformed payloads before the
        use case is even reached.
        """
        customer_id = self._require_str(raw, "customer_id")
        raw_items: List[Dict[str, Any]] = self._require_list(raw, "items")

        items = [self._parse_item(i, idx) for idx, i in enumerate(raw_items)]

        request = CreateOrderRequest(customer_id=customer_id, items=items)
        self._interactor.execute(request)

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _require_str(data: Dict[str, Any], key: str) -> str:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ControllerValidationError(f"'{key}' must be a non-empty string")
        return value.strip()

    @staticmethod
    def _require_list(data: Dict[str, Any], key: str) -> list:
        value = data.get(key)
        if not isinstance(value, list) or len(value) == 0:
            raise ControllerValidationError(f"'{key}' must be a non-empty list")
        return value

    @staticmethod
    def _parse_item(raw_item: Dict[str, Any], idx: int) -> OrderItemRequest:
        prefix = f"items[{idx}]"

        product_id = raw_item.get("product_id")
        if not isinstance(product_id, str) or not product_id.strip():
            raise ControllerValidationError(f"{prefix}.product_id must be a non-empty string")

        quantity = raw_item.get("quantity")
        if not isinstance(quantity, int):
            raise ControllerValidationError(f"{prefix}.quantity must be an integer")

        raw_price = raw_item.get("unit_price")
        try:
            unit_price = Decimal(str(raw_price))
        except (InvalidOperation, TypeError):
            raise ControllerValidationError(
                f"{prefix}.unit_price must be a valid decimal number"
            )

        return OrderItemRequest(
            product_id=product_id.strip(),
            quantity=quantity,
            unit_price=unit_price,
        )


class ControllerValidationError(Exception):
    """Raised by the controller when the incoming payload is malformed."""
