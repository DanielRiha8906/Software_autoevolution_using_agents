"""Core calculation engine module.

This module contains the pure calculation logic, separated from
storage, history tracking, and CLI concerns.
"""

from .calculation_engine import CalculationEngine

__all__ = ["CalculationEngine"]
