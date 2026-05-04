from dataclasses import dataclass, field


@dataclass
class ImportResult:
    """Result of an import operation with success/error tracking."""

    total: int
    imported: int
    skipped: int
    errors: list = field(default_factory=list)
    updated: int = 0

    @property
    def error_count(self) -> int:
        """Return the count of errors."""
        return len(self.errors)

    @property
    def skipped_count(self) -> int:
        """Alias for skipped field."""
        return self.skipped

    def is_success(self) -> bool:
        """Return True if there are no errors."""
        return self.error_count == 0

    def summary(self) -> str:
        """Return a human-readable report string."""
        lines = [
            f"Import Summary:",
            f"  Total:    {self.total}",
            f"  Imported: {self.imported}",
            f"  Updated:  {self.updated}",
            f"  Skipped:  {self.skipped}",
            f"  Errors:   {self.error_count}",
        ]
        return "\n".join(lines)
