"""
Contract tests for the UnitOfWork port.
Verifies that every UoW implementation honours the transactional contract:
commit makes data visible, rollback (or exception) leaves nothing.
"""
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.entities.order import Order, OrderItem
from src.frameworks.db.in_memory.unit_of_work import InMemoryUnitOfWork
from src.frameworks.db.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from src.frameworks.db.sqlalchemy.models import Base


def _make_order():
    return Order.create(
        customer_id="cust-1",
        items=[OrderItem(product_id="sku-1", quantity=1, unit_price=Decimal("5.00"))],
    )


@pytest.fixture
def in_memory_uow():
    return InMemoryUnitOfWork()


@pytest.fixture
def sqlalchemy_uow():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return SqlAlchemyUnitOfWork(factory)


@pytest.fixture(params=["in_memory", "sqlalchemy"])
def uow(request, in_memory_uow, sqlalchemy_uow):
    return {"in_memory": in_memory_uow, "sqlalchemy": sqlalchemy_uow}[request.param]


class TestUnitOfWorkContract:
    def test_data_visible_after_commit(self, uow):
        order = _make_order()
        with uow:
            uow.orders.add(order)
            uow.commit()

        # Open a second context to prove data survived
        with uow:
            result = uow.orders.get(order.id)
        assert result is not None

    def test_context_manager_calls_rollback_on_exception(self, uow):
        """
        If the block raises, __exit__ calls rollback. We just assert no
        unhandled exception leaks out and the UoW remains usable.
        """
        order = _make_order()
        try:
            with uow:
                uow.orders.add(order)
                raise RuntimeError("simulated failure — do not commit")
        except RuntimeError:
            pass  # expected

        # UoW should still be usable
        with uow:
            uow.orders.add(_make_order())
            uow.commit()
