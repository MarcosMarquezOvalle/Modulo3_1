"""
Layer 2 – Use Cases: CreateOrder Interactor
===========================================
Application-specific business rules. Orchestrates entities, the Unit of
Work, and optional side-effecting gateways. Hands the result to the output
boundary (presenter) — it never returns a value directly.

Dependency rule: imports only from Layer 1 (entities) and ports defined in
the same layer. No framework, no SQLAlchemy, no HTTP.
"""
from __future__ import annotations

import logging
from typing import Optional

from src.entities.order import Order, OrderItem
from src.use_cases.ports import (
    CreateOrderResponseModel,
    NotificationGateway,
    OutputBoundary,
    UnitOfWork,
)
from src.use_cases.create_order.request_model import CreateOrderRequest

logger = logging.getLogger(__name__)


class CreateOrderInteractor:
    """
    Input boundary for the CreateOrder use case.

    The interactor:
    1. Translates the request model into domain entities.
    2. Persists the aggregate via the Unit of Work.
    3. Triggers an optional notification gateway (fire-and-forget; failure
       does NOT roll back the order — this is an accepted design trade-off).
    4. Hands a response model to the output boundary (presenter).
    """

    def __init__(
        self,
        uow: UnitOfWork,
        presenter: OutputBoundary,
        notifier: Optional[NotificationGateway] = None,
    ) -> None:
        self._uow = uow
        self._presenter = presenter
        self._notifier = notifier

    def execute(self, request: CreateOrderRequest) -> None:
        try:
            items = [
                OrderItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
                for item in request.items
            ]
            order = Order.create(customer_id=request.customer_id, items=items)

            with self._uow:
                self._uow.orders.add(order)
                self._uow.commit()

        except Exception as exc:
            self._presenter.present_error(exc)
            return

        self._fire_notification(order)

        self._presenter.present_success(
            CreateOrderResponseModel(
                order_id=order.id,
                customer_id=order.customer_id,
                status=order.status.value,
                total=order.total,
                item_count=len(order.items),
            )
        )

    def _fire_notification(self, order: Order) -> None:
        if self._notifier is None:
            return
        try:
            self._notifier.notify_order_created(order)
        except Exception:
            logger.exception(
                "Notification failed for order %s — order was persisted successfully.",
                order.id,
            )
