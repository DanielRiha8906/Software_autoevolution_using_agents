"""Adapter layer - external system integration.

This layer contains adapters for external systems (GitHub, APIs, etc.):
- GitHubAdapter: Handles GitHub API communication via gh CLI tool

Adapters are intentionally isolated from the business logic (service) layer
to keep external dependencies and their protocols separate. Services may use
adapters indirectly through facade services (e.g., GitHubFetchService delegates
to GitHubAdapter for actual API calls).

This separation makes it easier to:
- Mock or replace external integrations in tests
- Swap external service implementations
- Keep external API concerns isolated
- Maintain clean architecture boundaries
"""

from .github_adapter import GitHubAdapter

__all__ = ["GitHubAdapter"]
