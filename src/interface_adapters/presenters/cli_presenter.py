"""
Layer 3 – Interface Adapters: CLI Presenter
===========================================
Converts the use-case output into a human-readable string suitable for a
terminal. Demonstrates that the same use case can be driven by completely
different presenters without any change to the interactor.
"""
from __future__ import annotations

from typing import Optional

from src.use_cases.ports import CreateOrderResponseModel, OutputBoundary


class CliPresenter(OutputBoundary):
    """Produces a plain-text view model for terminal output."""

    def __init__(self) -> None:
        self._output: Optional[str] = None
        self._exit_code: int = 0

    @property
    def output(self) -> str:
        return self._output or ""

    @property
    def exit_code(self) -> int:
        return self._exit_code

    def present_success(self, response_model: CreateOrderResponseModel) -> None:
        self._exit_code = 0
        self._output = (
            f"✔ Order created successfully\n"
            f"  ID       : {response_model.order_id}\n"
            f"  Customer : {response_model.customer_id}\n"
            f"  Items    : {response_model.item_count}\n"
            f"  Total    : ${response_model.total:.2f}\n"
            f"  Status   : {response_model.status}"
        )

    def present_error(self, error: Exception) -> None:
        self._exit_code = 1
        self._output = f"✘ Failed to create order: {error}"
