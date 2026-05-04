"""Storage abstraction layer for TODO application.

This layer defines the storage interface and concrete implementations.
It separates persistence concerns from domain logic.
"""

from .protocols import StorageProtocol
from .json_storage import JsonStorage

__all__ = ["StorageProtocol", "JsonStorage"]
