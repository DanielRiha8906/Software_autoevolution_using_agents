"""Backward compatibility shim for Calculator.

The Calculator class has been moved to src.core.calculator.
This module provides imports for backward compatibility with existing imports.
"""
from ..core.calculator import Calculator

__all__ = ["Calculator"]
