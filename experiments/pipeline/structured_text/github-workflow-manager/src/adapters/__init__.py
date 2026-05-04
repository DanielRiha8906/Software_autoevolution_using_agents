"""
Adapters for external system integration.

This package contains adapters that integrate with external systems
(e.g., GitHub API, GitHub CLI) while maintaining separation from
core service and storage layers.
"""

from .github.api_client import GitHubApiClient
from .github.cli_adapter import GitHubCliAdapter
from .github.token_resolver import GitHubTokenResolver
from .github.converter import GitHubToWorkflowConverter

__all__ = [
    "GitHubApiClient",
    "GitHubCliAdapter",
    "GitHubTokenResolver",
    "GitHubToWorkflowConverter",
]
