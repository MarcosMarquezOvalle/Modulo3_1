"""
Layer 4 – Frameworks: HTTP Notification Simulator Gateway
=========================================================
Simulates an outbound HTTP webhook without real network I/O. Implements
NotificationGateway so it can be swapped for a real httpx/requests adapter
behind the same interface.
"""
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import List

from src.entities.order import Order
from src.use_cases.ports import NotificationGateway

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class _SimulatedResponse:
    status_code: int


class HttpNotificationSimulatorGateway(NotificationGateway):
    """
    Simulates a POST to a webhook endpoint.

    Parameters
    ----------
    endpoint:       The URL that would be called in production.
    failure_rate:   0.0 = always succeeds, 1.0 = always fails (500).
    latency:        Artificial sleep to model network delay (seconds).
    """

    def __init__(
        self,
        endpoint: str = "https://notifications.example.com/webhooks/orders",
        failure_rate: float = 0.0,
        latency: float = 0.0,
    ) -> None:
        self._endpoint = endpoint
        self._failure_rate = failure_rate
        self._latency = latency
        self.captured: List[dict] = []   # inspectable in tests

    def notify_order_created(self, order: Order) -> None:
        payload = {
            "event": "order.created",
            "order_id": str(order.id),
            "customer_id": order.customer_id,
            "status": order.status.value,
            "total": str(order.total),
            "items": [
                {
                    "product_id": i.product_id,
                    "quantity": i.quantity,
                    "unit_price": str(i.unit_price),
                }
                for i in order.items
            ],
        }

        if self._latency:
            time.sleep(self._latency)

        response = self._simulate_post()
        self.captured.append({"endpoint": self._endpoint, "payload": payload,
                               "status_code": response.status_code})

        if response.status_code >= 400:
            raise NotificationError(
                response.status_code,
                f"Simulated POST to {self._endpoint} returned {response.status_code}",
            )

        logger.info("Notification sent for order %s → %s", order.id, response.status_code)

    def _simulate_post(self) -> _SimulatedResponse:
        code = 500 if random.random() < self._failure_rate else 200
        return _SimulatedResponse(status_code=code)
