"""GitHub REST API fetcher - backward compatibility re-export."""

from ..adapters.github.api_fetcher import GitHubAPIFetcher
from ..adapters.github import api_fetcher
import requests

__all__ = ["GitHubAPIFetcher"]
