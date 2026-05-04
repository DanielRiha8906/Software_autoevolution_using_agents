"""Storage abstraction layer for the TODO application.

This layer handles all persistence concerns, providing a simple interface
for loading and saving data.
"""

from .json_storage import JsonStorage

__all__ = ["JsonStorage"]
