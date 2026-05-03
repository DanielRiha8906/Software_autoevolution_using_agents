class ValidationError(Exception):
    """Custom exception for validation errors with single/multi-message support."""

    def __init__(self, messages=None):
        """Initialize ValidationError with single or multiple messages.

        Args:
            messages: A string message or list of error message strings
        """
        if isinstance(messages, str):
            self._messages = [messages]
        elif isinstance(messages, list):
            self._messages = messages if messages else []
        else:
            self._messages = []
        super().__init__(self._get_summary())

    def _get_summary(self) -> str:
        """Return a summary string of all messages."""
        if not self._messages:
            return "Validation error"
        if len(self._messages) == 1:
            return self._messages[0]
        return f"Validation error ({len(self._messages)} errors): {'; '.join(self._messages)}"

    @property
    def message(self) -> str:
        """Return the first error message."""
        return self._messages[0] if self._messages else ""

    @property
    def messages(self) -> list:
        """Return all error messages as a list."""
        return list(self._messages)

    def __str__(self) -> str:
        """Return human-readable error representation."""
        if not self._messages:
            return "Validation error"
        error_count = len(self._messages)
        if error_count == 1:
            return f"Validation error: {self._messages[0]}"
        return f"Validation error ({error_count} errors): {'; '.join(self._messages)}"
