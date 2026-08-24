"""
Layer 2 – Use Cases: Ports
==========================
Abstract interfaces declared by the use-case layer that outer layers must
implement. Nothing here imports SQLAlchemy, requests, Flask, etc.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.entities.order import Order


# ---------------------------------------------------------------------------
# Repository port
# ---------------------------------------------------------------------------

class OrderRepository(ABC):
    """Persistence contract for Order aggregates."""

    @abstractmethod
    def add(self, order: Order) -> None: ...

    @abstractmethod
    def get(self, order_id: UUID) -> Optional[Order]: ...

    @abstractmethod
    def list_by_customer(self, customer_id: str) -> List[Order]: ...


# ---------------------------------------------------------------------------
# Unit of Work port
# ---------------------------------------------------------------------------

class UnitOfWork(ABC):
    """
    Demarcates a transactional boundary. The use case obtains the repository
    via ``uow.orders`` and calls ``uow.commit()`` / ``uow.rollback()``
    explicitly.  Implements the context-manager protocol so it can be used as::

        with uow:
            uow.orders.add(order)
            uow.commit()
    """
    orders: OrderRepository  # set by the concrete implementation

    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, *exc) -> None:
        if exc[0] is not None:
            self.rollback()

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...


# ---------------------------------------------------------------------------
# Notification port
# ---------------------------------------------------------------------------

class NotificationGateway(ABC):
    """Contract for notifying external systems (webhook, queue, email…)."""

    @abstractmethod
    def notify_order_created(self, order: Order) -> None: ...


# ---------------------------------------------------------------------------
# Output boundary (Presenter port)
# ---------------------------------------------------------------------------

class OutputBoundary(ABC):
    """
    Use cases depend on this interface to hand results back to the caller.
    The concrete presenter (in the interface-adapters layer) converts the
    use-case output into whatever format the delivery mechanism needs
    (JSON dict, CLI string, view model, etc.).
    """

    @abstractmethod
    def present_success(self, response_model: "CreateOrderResponseModel") -> None: ...

    @abstractmethod
    def present_error(self, error: Exception) -> None: ...


# ---------------------------------------------------------------------------
# Response model (plain data produced by the use case)
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CreateOrderResponseModel:
    """
    Plain data object produced by the use case and handed to the presenter.
    No formatting, no framework types.
    """
    order_id: UUID
    customer_id: str
    status: str
    total: Decimal
    item_count: int
