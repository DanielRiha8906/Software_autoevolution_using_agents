"""Storage layer for persistence operations.

This module provides concrete implementations of storage backends.
The actual storage logic is decoupled from service layers via Protocol definitions.
"""

from .json_storage import JsonStorage

__all__ = ["JsonStorage"]
