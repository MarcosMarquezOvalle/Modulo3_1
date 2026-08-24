"""SQLAlchemy implementation of the OrderRepository port."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.entities.order import Order, OrderItem, OrderStatus
from src.use_cases.ports import OrderRepository
from src.frameworks.db.sqlalchemy.models import OrderItemModel, OrderModel


class SqlAlchemyOrderGateway(OrderRepository):
    """
    Translates between the domain model (Order aggregate) and the SQLAlchemy
    ORM models. The Session is injected by the Unit of Work — this class
    never manages transaction boundaries itself.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, order: Order) -> None:
        self._session.add(
            OrderModel(
                id=order.id,
                customer_id=order.customer_id,
                status=order.status.value,
                created_at=order.created_at,
                items=[
                    OrderItemModel(
                        product_id=i.product_id,
                        quantity=i.quantity,
                        unit_price=i.unit_price,
                    )
                    for i in order.items
                ],
            )
        )

    def get(self, order_id: UUID) -> Optional[Order]:
        model = self._session.get(OrderModel, order_id)
        return self._to_domain(model) if model else None

    def list_by_customer(self, customer_id: str) -> List[Order]:
        rows = (
            self._session.query(OrderModel)
            .filter(OrderModel.customer_id == customer_id)
            .all()
        )
        return [self._to_domain(r) for r in rows]

    @staticmethod
    def _to_domain(m: OrderModel) -> Order:
        return Order(
            id=m.id,
            customer_id=m.customer_id,
            status=OrderStatus(m.status),
            created_at=m.created_at,
            items=[
                OrderItem(
                    product_id=i.product_id,
                    quantity=i.quantity,
                    unit_price=i.unit_price,
                )
                for i in m.items
            ],
        )
