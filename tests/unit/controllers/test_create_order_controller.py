"""Unit tests for CreateOrderController — verifies parsing and validation."""
import pytest

from src.interface_adapters.controllers.create_order_controller import (
    CreateOrderController,
    ControllerValidationError,
)
from src.use_cases.create_order.interactor import CreateOrderInteractor
from src.interface_adapters.presenters.json_presenter import JsonPresenter
from src.frameworks.db.in_memory.unit_of_work import InMemoryUnitOfWork


def _make_controller():
    presenter = JsonPresenter()
    interactor = CreateOrderInteractor(
        uow=InMemoryUnitOfWork(),
        presenter=presenter,
    )
    return CreateOrderController(interactor), presenter


VALID_PAYLOAD = {
    "customer_id": "cust-1",
    "items": [{"product_id": "sku-1", "quantity": 2, "unit_price": "10.00"}],
}


def test_valid_payload_creates_order():
    ctrl, presenter = _make_controller()
    ctrl.handle(VALID_PAYLOAD)
    assert presenter.view.success is True


def test_missing_customer_id_raises_validation_error():
    ctrl, _ = _make_controller()
    with pytest.raises(ControllerValidationError, match="customer_id"):
        ctrl.handle({"items": [{"product_id": "sku-1", "quantity": 1, "unit_price": "1.00"}]})


def test_empty_items_list_raises_validation_error():
    ctrl, _ = _make_controller()
    with pytest.raises(ControllerValidationError, match="items"):
        ctrl.handle({"customer_id": "cust-1", "items": []})


def test_missing_product_id_raises_validation_error():
    ctrl, _ = _make_controller()
    with pytest.raises(ControllerValidationError, match="product_id"):
        ctrl.handle({"customer_id": "c", "items": [{"quantity": 1, "unit_price": "1.00"}]})


def test_invalid_unit_price_raises_validation_error():
    ctrl, _ = _make_controller()
    with pytest.raises(ControllerValidationError, match="unit_price"):
        ctrl.handle({"customer_id": "c", "items": [
            {"product_id": "sku-1", "quantity": 1, "unit_price": "not-a-number"}
        ]})


def test_non_integer_quantity_raises_validation_error():
    ctrl, _ = _make_controller()
    with pytest.raises(ControllerValidationError, match="quantity"):
        ctrl.handle({"customer_id": "c", "items": [
            {"product_id": "sku-1", "quantity": "two", "unit_price": "1.00"}
        ]})
