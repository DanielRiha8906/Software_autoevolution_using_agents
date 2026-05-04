"""GitHub Auth Manager - backward compatibility re-export."""

from ..adapters.github.auth import GitHubAuthManager as _GitHubAuthManager
from ..adapters.github import auth
from getpass import getpass

class GitHubAuthManager(_GitHubAuthManager):
    """Wrapper for backward compatibility that allows getpass to be patched."""

    def _prompt_for_token(self):
        """Override to use getpass from this module's namespace."""
        try:
            token = getpass(
                "GitHub token not found. Enter your GitHub Personal Access Token "
                "(hidden input): "
            )
            if token:
                return token
        except (KeyboardInterrupt, EOFError):
            pass
        return None

__all__ = ["GitHubAuthManager"]
