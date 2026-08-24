# CreateOrder — Clean Architecture

A Python implementation of Uncle Bob's **Clean Architecture** built around
the `CreateOrder` use case. The project is split into four concentric layers;
each layer may only depend on layers *inside* it.

```
┌─────────────────────────────────────────────────────────┐
│  4. Frameworks & Drivers                                │
│  (SQLAlchemy, in-memory, HTTP simulator)                │
│  ┌───────────────────────────────────────────────────┐  │
│  │  3. Interface Adapters                            │  │
│  │  Controllers · Presenters · Gateways              │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │  2. Use Cases (Interactors)                 │  │  │
│  │  │  CreateOrderInteractor · Ports · UoW        │  │  │
│  │  │  ┌───────────────────────────────────────┐  │  │  │
│  │  │  │  1. Entities                          │  │  │  │
│  │  │  │  Order · OrderItem · Exceptions       │  │  │  │
│  │  │  └───────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Project structure

```
src/
  entities/                    Layer 1 — Enterprise business rules
    order.py                     Order aggregate, OrderItem value object
    exceptions.py

  use_cases/                   Layer 2 — Application business rules
    ports.py                     Abstract ports: OrderRepository, UnitOfWork,
                                 NotificationGateway, OutputBoundary
    create_order/
      request_model.py           Input DTO (CreateOrderRequest)
      interactor.py              CreateOrderInteractor (the use case)

  interface_adapters/          Layer 3 — Adapters between use cases and I/O
    controllers/
      create_order_controller.py  Parses raw dicts → request model
    presenters/
      json_presenter.py           Converts response model → JSON-ready dict
      cli_presenter.py            Converts response model → terminal string
    gateways/                     (re-export package)

  frameworks/                  Layer 4 — Concrete infrastructure
    db/
      sqlalchemy/
        models.py                ORM models
        order_gateway.py         SqlAlchemyOrderGateway
        unit_of_work.py          SqlAlchemyUnitOfWork
      in_memory/
        order_gateway.py         InMemoryOrderGateway
        unit_of_work.py          InMemoryUnitOfWork
    notifications/
      http_simulator.py          HttpNotificationSimulatorGateway

tests/
  unit/
    use_cases/                   Interactor tests (in-memory, fast)
    presenters/                  Presenter tests (pure unit)
    controllers/                 Controller parsing/validation tests
  contract/
    test_order_repository_contract.py   Same suite → all OrderRepository adapters
    test_unit_of_work_contract.py       Same suite → all UoW adapters
    test_notification_gateway_contract.py
```

## Key design decisions

### Presenter / Output Boundary
The interactor **never returns a value**. Instead it calls
`presenter.present_success(response_model)` or `presenter.present_error(exc)`.
The controller then reads `presenter.view` to get the framework-specific
representation. This keeps the use case independent of HTTP, JSON, or any
other output format.

### Unit of Work
The interactor receives a `UnitOfWork` port, opens it with `with uow:`, calls
`uow.commit()` on success, and relies on `__exit__` to call `rollback()` on
exception. The repository is accessed as `uow.orders`, so the transaction
boundary and the repository are always paired.

### Notification resilience
`CreateOrderInteractor` fires the notification *after* committing the UoW.
A notification failure is caught and logged — it never rolls back an
already-persisted order. Production systems would add an outbox / retry
mechanism here.

### Contract testing
Every abstract port (`OrderRepository`, `UnitOfWork`, `NotificationGateway`)
has a corresponding contract-test class. The test class is parametrized over
all concrete adapters. A new adapter must pass the full contract before it can
be wired in production.

## Running

```bash
pip install -r requirements.txt
pytest                    # all tests
pytest tests/unit -v      # unit tests only
pytest tests/contract -v  # contract tests (each runs per adapter)
```

## Wiring example

```python
from src.frameworks.db.sqlalchemy.unit_of_work import build_sqlite_uow
from src.frameworks.notifications.http_simulator import HttpNotificationSimulatorGateway
from src.interface_adapters.presenters.json_presenter import JsonPresenter
from src.interface_adapters.controllers.create_order_controller import CreateOrderController
from src.use_cases.create_order.interactor import CreateOrderInteractor

uow       = build_sqlite_uow("sqlite:///orders.db")   # swap for Postgres URL in prod
notifier  = HttpNotificationSimulatorGateway()          # swap for real HTTP gateway
presenter = JsonPresenter()
interactor = CreateOrderInteractor(uow, presenter, notifier)
controller = CreateOrderController(interactor)

controller.handle({
    "customer_id": "cust-1",
    "items": [{"product_id": "sku-1", "quantity": 2, "unit_price": "19.99"}],
})

print(presenter.view)   # JsonViewModel(success=True, status_code=201, data={...})
```
