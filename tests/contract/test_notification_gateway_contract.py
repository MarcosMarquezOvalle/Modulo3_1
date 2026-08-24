"""Contract tests for the NotificationGateway port."""
from decimal import Decimal

import pytest

from src.entities.order import Order, OrderItem
from src.frameworks.notifications.http_simulator import (
    HttpNotificationSimulatorGateway,
    NotificationError,
)


def _make_order():
    return Order.create(
        customer_id="cust-1",
        items=[OrderItem(product_id="sku-1", quantity=2, unit_price=Decimal("7.50"))],
    )


@pytest.fixture(params=["http_simulator"])
def gateway(request):
    return {
        "http_simulator": HttpNotificationSimulatorGateway(failure_rate=0.0),
    }[request.param]


class TestNotificationGatewayContract:
    def test_successful_notification_is_captured(self, gateway):
        order = _make_order()
        gateway.notify_order_created(order)
        assert len(gateway.captured) == 1
        assert gateway.captured[0]["payload"]["order_id"] == str(order.id)
        assert gateway.captured[0]["status_code"] == 200

    def test_failure_raises_notification_error(self):
        failing = HttpNotificationSimulatorGateway(failure_rate=1.0)
        with pytest.raises(NotificationError) as exc_info:
            failing.notify_order_created(_make_order())
        assert exc_info.value.status_code == 500
