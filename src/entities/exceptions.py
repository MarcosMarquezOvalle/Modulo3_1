"""Domain exceptions — raised by entities and re-raised by use cases."""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: object) -> None:
        super().__init__(f"Order '{order_id}' not found.")
        self.order_id = order_id


class InvalidOrderError(DomainError):
    """Raised when an order violates a domain invariant."""
