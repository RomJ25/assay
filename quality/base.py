"""Abstract base class for quality/growth models."""

from __future__ import annotations

from abc import ABC, abstractmethod

from data.providers.base import FinancialData


class QualityModel(ABC):
    """Base class for quality models (Piotroski, Growth)."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def calculate(self, data: FinancialData) -> float | None:
        """Calculate a 0-100 quality score.

        Returns None if model is not applicable.
        """
        ...
