"""
Layer 1 – Entities
==================
Enterprise business rules that are completely independent of any framework,
database, or delivery mechanism. They contain the highest-level rules and
have no outward dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from uuid import UUID, uuid4


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class OrderItem:
    product_id: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be greater than zero")
        if self.unit_price < Decimal("0"):
            raise ValueError("unit_price cannot be negative")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    id: UUID
    customer_id: str
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("an order must contain at least one item")
        if not self.customer_id:
            raise ValueError("customer_id is required")

    # ------------------------------------------------------------------ #
    # Business rules (the only logic that lives inside an Entity)
    # ------------------------------------------------------------------ #
    @property
    def total(self) -> Decimal:
        return sum((i.subtotal for i in self.items), Decimal("0"))

    def confirm(self) -> None:
        if self.status != OrderStatus.CREATED:
            raise ValueError(f"cannot confirm an order with status {self.status}")
        self.status = OrderStatus.CONFIRMED

    def cancel(self) -> None:
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("order is already cancelled")
        self.status = OrderStatus.CANCELLED

    # ------------------------------------------------------------------ #
    # Factory
    # ------------------------------------------------------------------ #
    @classmethod
    def create(cls, customer_id: str, items: List[OrderItem]) -> "Order":
        return cls(id=uuid4(), customer_id=customer_id, items=items)
