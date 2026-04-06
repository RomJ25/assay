"""Abstract base class for valuation models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from data.providers.base import FinancialData


@dataclass
class ValuationResult:
    """Result from a valuation model."""
    intrinsic_value: float | None  # per-share intrinsic value (None = not applicable)
    details: dict = None  # additional details (e.g., bear/base/bull for DCF)

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ValuationModel(ABC):
    """Base class for value models (DCF, Graham, Relative)."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def calculate(self, data: FinancialData) -> ValuationResult:
        """Calculate intrinsic value for a stock.

        Returns ValuationResult with intrinsic_value per share,
        or intrinsic_value=None if model is not applicable.
        """
        ...
