from dataclasses import dataclass
from typing import List


@dataclass
class ImportResult:
    """Result metadata from an import operation."""
    filepath: str
    total_records: int
    imported_runs: int
    skipped_runs: int
    imported_attempts: int
    skipped_attempts: int
    errors: List[str]
    had_overwrite: bool
