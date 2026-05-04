"""Backward compatibility shim for StatisticsService.

The StatisticsService class has been moved to src.history.statistics_service.
This module provides imports for backward compatibility with existing imports.
"""
from ..history.statistics_service import StatisticsService

__all__ = ["StatisticsService"]
