"""History and memory management module.

This module handles storage and retrieval of calculation results and
memory entries, separated from the calculation engine and CLI concerns.
"""

from .memory_manager import MemoryManager

__all__ = ["MemoryManager"]
