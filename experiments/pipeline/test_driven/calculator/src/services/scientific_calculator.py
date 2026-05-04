"""Backward compatibility shim for ScientificCalculator.

The ScientificCalculator class has been moved to src.core.scientific_calculator.
This module provides imports for backward compatibility with existing imports.
"""
from ..core.scientific_calculator import ScientificCalculator

__all__ = ["ScientificCalculator"]
