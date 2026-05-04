"""JSON storage implementation for TODO application.

This module re-exports the JsonStorage implementation from the storage layer
for backward compatibility.
"""

from ..layers.storage.json_storage import JsonStorage

__all__ = ["JsonStorage"]
