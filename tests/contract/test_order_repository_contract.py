"""
Contract tests for the OrderRepository port.
Runs the same assertions against every gateway adapter.
Adding a new adapter = one new entry in the fixture parameters.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.entities.order import Order, OrderItem
from src.frameworks.db.in_memory.order_gateway import InMemoryOrderGateway
from src.frameworks.db.sqlalchemy.models import Base
from src.frameworks.db.sqlalchemy.order_gateway import SqlAlchemyOrderGateway


def _make_order(customer_id: str = "cust-A") -> Order:
    return Order.create(
        customer_id=customer_id,
        items=[OrderItem(product_id="sku-1", quantity=1, unit_price=Decimal("9.99"))],
    )


@pytest.fixture
def in_memory_gw():
    return InMemoryOrderGateway()


@pytest.fixture
def sqlalchemy_gw():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield SqlAlchemyOrderGateway(session)
    session.close()


@pytest.fixture(params=["in_memory", "sqlalchemy"])
def gateway(request, in_memory_gw, sqlalchemy_gw):
    return {"in_memory": in_memory_gw, "sqlalchemy": sqlalchemy_gw}[request.param]


class TestOrderRepositoryContract:
    def test_add_and_get_round_trip(self, gateway):
        order = _make_order()
        gateway.add(order)
        result = gateway.get(order.id)
        assert result is not None
        assert result.id == order.id
        assert result.customer_id == order.customer_id
        assert result.total == order.total
        assert result.status == order.status

    def test_get_unknown_returns_none(self, gateway):
        assert gateway.get(uuid4()) is None

    def test_list_by_customer_filters(self, gateway):
        o1 = _make_order("cust-A")
        o2 = _make_order("cust-A")
        o3 = _make_order("cust-B")
        for o in (o1, o2, o3):
            gateway.add(o)
        result = gateway.list_by_customer("cust-A")
        assert {o.id for o in result} == {o1.id, o2.id}

    def test_list_by_customer_empty(self, gateway):
        assert gateway.list_by_customer("nobody") == []
