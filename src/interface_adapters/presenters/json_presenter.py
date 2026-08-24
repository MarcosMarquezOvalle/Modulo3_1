"""
Layer 3 – Interface Adapters: JSON Presenter
=============================================
Converts the use-case output model into a JSON-serialisable dict that an
HTTP controller (Flask, FastAPI, Django…) can return as a response body.

The presenter holds the "view model" — the result of the last presentation
— so the controller can call the interactor and then read ``presenter.view``
in two separate steps (Uncle Bob's recommended split).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.entities.exceptions import DomainError
from src.use_cases.ports import CreateOrderResponseModel, OutputBoundary


@dataclass
class JsonViewModel:
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class JsonPresenter(OutputBoundary):
    """Produces a JSON-friendly view model."""

    def __init__(self) -> None:
        self._view: Optional[JsonViewModel] = None

    @property
    def view(self) -> JsonViewModel:
        if self._view is None:
            raise RuntimeError("present_success or present_error has not been called yet")
        return self._view

    def present_success(self, response_model: CreateOrderResponseModel) -> None:
        self._view = JsonViewModel(
            success=True,
            status_code=201,
            data={
                "order_id": str(response_model.order_id),
                "customer_id": response_model.customer_id,
                "status": response_model.status,
                "total": str(response_model.total),
                "item_count": response_model.item_count,
            },
        )

    def present_error(self, error: Exception) -> None:
        is_domain = isinstance(error, (ValueError, DomainError))
        self._view = JsonViewModel(
            success=False,
            status_code=422 if is_domain else 500,
            error=str(error),
        )
