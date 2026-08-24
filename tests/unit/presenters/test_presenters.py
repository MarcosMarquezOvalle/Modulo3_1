"""Unit tests for JSON and CLI presenters — no use case needed."""
from decimal import Decimal
from uuid import uuid4

import pytest

from src.use_cases.ports import CreateOrderResponseModel
from src.interface_adapters.presenters.json_presenter import JsonPresenter
from src.interface_adapters.presenters.cli_presenter import CliPresenter
from src.entities.exceptions import DomainError


def _response_model(**kwargs):
    defaults = dict(
        order_id=uuid4(),
        customer_id="cust-1",
        status="CREATED",
        total=Decimal("25.50"),
        item_count=2,
    )
    return CreateOrderResponseModel(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# JsonPresenter
# ---------------------------------------------------------------------------

class TestJsonPresenter:
    def test_success_view_has_201_and_data(self):
        p = JsonPresenter()
        p.present_success(_response_model())
        assert p.view.success is True
        assert p.view.status_code == 201
        assert p.view.data is not None

    def test_success_serialises_uuid_as_string(self):
        oid = uuid4()
        p = JsonPresenter()
        p.present_success(_response_model(order_id=oid))
        assert p.view.data["order_id"] == str(oid)

    def test_success_serialises_decimal_as_string(self):
        p = JsonPresenter()
        p.present_success(_response_model(total=Decimal("99.99")))
        assert p.view.data["total"] == "99.99"

    def test_domain_error_yields_422(self):
        p = JsonPresenter()
        p.present_error(ValueError("bad input"))
        assert p.view.success is False
        assert p.view.status_code == 422
        assert "bad input" in p.view.error

    def test_generic_error_yields_500(self):
        p = JsonPresenter()
        p.present_error(RuntimeError("unexpected"))
        assert p.view.status_code == 500

    def test_raises_if_view_accessed_before_present(self):
        with pytest.raises(RuntimeError):
            _ = JsonPresenter().view


# ---------------------------------------------------------------------------
# CliPresenter
# ---------------------------------------------------------------------------

class TestCliPresenter:
    def test_success_exit_code_is_0(self):
        p = CliPresenter()
        p.present_success(_response_model())
        assert p.exit_code == 0

    def test_success_output_contains_order_id(self):
        oid = uuid4()
        p = CliPresenter()
        p.present_success(_response_model(order_id=oid))
        assert str(oid) in p.output

    def test_error_exit_code_is_1(self):
        p = CliPresenter()
        p.present_error(ValueError("oops"))
        assert p.exit_code == 1

    def test_error_output_contains_message(self):
        p = CliPresenter()
        p.present_error(ValueError("something went wrong"))
        assert "something went wrong" in p.output
