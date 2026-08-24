"""In-memory Unit of Work — no real transactions, ideal for fast tests."""
from __future__ import annotations

from src.use_cases.ports import UnitOfWork
from src.frameworks.db.in_memory.order_gateway import InMemoryOrderGateway


class InMemoryUnitOfWork(UnitOfWork):
    """
    Stateless UoW backed by a shared in-memory store.  Re-uses the *same*
    gateway instance on every ``__enter__`` so data written in one ``with``
    block is visible in the next, mimicking a persistent data source across
    the test scenario.
    """

    def __init__(self) -> None:
        self.orders = InMemoryOrderGateway()
        self._committed = False

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._committed = False
        return self

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        # In-memory: nothing to undo; a production implementation might
        # snapshot the store before each UoW and restore it here.
        pass

    @property
    def was_committed(self) -> bool:
        return self._committed
