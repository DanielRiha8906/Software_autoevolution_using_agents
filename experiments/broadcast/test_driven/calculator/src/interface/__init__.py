"""User interface and interaction layer.

This module handles all user-facing interactions (CLI, menus, prompts)
and is decoupled from calculation and storage concerns.
"""

from .user_interface import UserInterface

__all__ = ["UserInterface"]
