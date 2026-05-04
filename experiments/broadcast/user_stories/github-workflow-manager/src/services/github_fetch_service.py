"""Backward compatibility re-export of GitHubFetchService from adapters layer."""

from ..adapters.github_adapter import GitHubFetchService

__all__ = ["GitHubFetchService"]
