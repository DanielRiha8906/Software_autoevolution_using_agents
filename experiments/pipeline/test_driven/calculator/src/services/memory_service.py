"""Backward compatibility shim for MemoryService.

The MemoryService class has been moved to src.history.memory_service.
This module provides imports for backward compatibility with existing imports.
"""
from ..history.memory_service import MemoryService

__all__ = ["MemoryService"]
