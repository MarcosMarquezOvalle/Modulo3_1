"""Unit tests for CreateOrderInteractor — backed by in-memory adapters."""
from decimal import Decimal

import pytest

from src.use_cases.create_order.interactor import CreateOrderInteractor
from src.use_cases.create_order.request_model import CreateOrderRequest, OrderItemRequest
from src.frameworks.db.in_memory.unit_of_work import InMemoryUnitOfWork
from src.interface_adapters.presenters.json_presenter import JsonPresenter
from src.frameworks.notifications.http_simulator import (
    HttpNotificationSimulatorGateway,
    NotificationError,
)


def _make_request(customer_id: str = "cust-1", qty: int = 2, price: str = "10.00"):
    return CreateOrderRequest(
        customer_id=customer_id,
        items=[OrderItemRequest(product_id="sku-1", quantity=qty, unit_price=Decimal(price))],
    )


def build_interactor(uow=None, presenter=None, notifier=None):
    return CreateOrderInteractor(
        uow=uow or InMemoryUnitOfWork(),
        presenter=presenter or JsonPresenter(),
        notifier=notifier,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_success_presents_201_with_correct_data():
    presenter = JsonPresenter()
    uow = InMemoryUnitOfWork()
    interactor = build_interactor(uow=uow, presenter=presenter)

    interactor.execute(_make_request(qty=3, price="5.00"))

    vm = presenter.view
    assert vm.success is True
    assert vm.status_code == 201
    assert vm.data["customer_id"] == "cust-1"
    assert vm.data["total"] == "15.00"
    assert vm.data["item_count"] == 1


def test_uow_is_committed_on_success():
    uow = InMemoryUnitOfWork()
    build_interactor(uow=uow).execute(_make_request())
    assert uow.was_committed is True


def test_order_is_retrievable_after_commit():
    uow = InMemoryUnitOfWork()
    presenter = JsonPresenter()
    build_interactor(uow=uow, presenter=presenter).execute(_make_request())

    order_id_str = presenter.view.data["order_id"]
    from uuid import UUID
    order = uow.orders.get(UUID(order_id_str))
    assert order is not None
    assert order.customer_id == "cust-1"


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------

def test_empty_items_presents_error():
    presenter = JsonPresenter()
    req = CreateOrderRequest(customer_id="cust-1", items=[])
    build_interactor(presenter=presenter).execute(req)

    vm = presenter.view
    assert vm.success is False
    assert vm.status_code == 422


def test_negative_quantity_presents_error():
    presenter = JsonPresenter()
    req = CreateOrderRequest(
        customer_id="cust-1",
        items=[OrderItemRequest(product_id="sku-1", quantity=-1, unit_price=Decimal("1.00"))],
    )
    build_interactor(presenter=presenter).execute(req)

    assert presenter.view.success is False
    assert presenter.view.status_code == 422


# ---------------------------------------------------------------------------
# Notification side-effect
# ---------------------------------------------------------------------------

def test_notification_is_sent_on_success():
    notifier = HttpNotificationSimulatorGateway(failure_rate=0.0)
    build_interactor(notifier=notifier).execute(_make_request())

    assert len(notifier.captured) == 1
    assert notifier.captured[0]["payload"]["event"] == "order.created"


def test_order_is_persisted_even_when_notification_fails():
    uow = InMemoryUnitOfWork()
    presenter = JsonPresenter()
    notifier = HttpNotificationSimulatorGateway(failure_rate=1.0)

    build_interactor(uow=uow, presenter=presenter, notifier=notifier).execute(_make_request())

    # The order creation itself succeeded
    assert presenter.view.success is True
    assert uow.was_committed is True
