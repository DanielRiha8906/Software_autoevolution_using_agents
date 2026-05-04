"""Backward compatibility shim for ImportExportService.

The ImportExportService class has been moved to src.history.import_export_service.
This module provides imports for backward compatibility with existing imports.
"""
from ..history.import_export_service import ImportExportService

__all__ = ["ImportExportService"]
