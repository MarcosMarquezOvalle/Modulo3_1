"""SQLAlchemy implementation of the UnitOfWork port."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.use_cases.ports import UnitOfWork
from src.frameworks.db.sqlalchemy.order_gateway import SqlAlchemyOrderGateway
from src.frameworks.db.sqlalchemy.models import Base


class SqlAlchemyUnitOfWork(UnitOfWork):
    """
    Wraps a SQLAlchemy Session as a transactional unit of work.

    Usage::

        uow = SqlAlchemyUnitOfWork(session_factory)
        with uow:
            uow.orders.add(order)
            uow.commit()       # flush + commit
            # on exception → __exit__ calls rollback()
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        self._factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session: Session = self._factory()
        self.orders = SqlAlchemyOrderGateway(self._session)
        return self

    def __exit__(self, *exc) -> None:
        super().__exit__(*exc)
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


# ---------------------------------------------------------------------------
# Convenience factory for SQLite (tests) and any SQLAlchemy-compatible URL
# ---------------------------------------------------------------------------

def build_sqlite_uow(url: str = "sqlite:///:memory:") -> SqlAlchemyUnitOfWork:
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return SqlAlchemyUnitOfWork(sessionmaker(bind=engine))
