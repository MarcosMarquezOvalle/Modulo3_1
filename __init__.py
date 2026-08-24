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