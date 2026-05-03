"""Tests for GitHub-specific exceptions."""

import pytest

from src.exceptions import (
    GitHubAuthError,
    GitHubAPIError,
    GitHubNetworkError,
    GitHubRateLimitError,
)


class TestGitHubAuthException:
    """Test GitHubAuthError exception."""

    def test_auth_error_is_exception(self):
        """GitHubAuthError should be an Exception."""
        assert issubclass(GitHubAuthError, Exception)

    def test_auth_error_can_be_raised(self):
        """GitHubAuthError should be raisable."""
        with pytest.raises(GitHubAuthError):
            raise GitHubAuthError("Invalid token")

    def test_auth_error_message(self):
        """GitHubAuthError should preserve message."""
        error_msg = "Authentication failed: expired token"
        with pytest.raises(GitHubAuthError) as exc_info:
            raise GitHubAuthError(error_msg)
        assert str(exc_info.value) == error_msg

    def test_auth_error_inheritance_chain(self):
        """GitHubAuthError should inherit from Exception."""
        error = GitHubAuthError("Test")
        assert isinstance(error, Exception)


class TestGitHubAPIException:
    """Test GitHubAPIError exception."""

    def test_api_error_is_exception(self):
        """GitHubAPIError should be an Exception."""
        assert issubclass(GitHubAPIError, Exception)

    def test_api_error_can_be_raised(self):
        """GitHubAPIError should be raisable."""
        with pytest.raises(GitHubAPIError):
            raise GitHubAPIError("API request failed")

    def test_api_error_message(self):
        """GitHubAPIError should preserve message."""
        error_msg = "Repository not found: owner/repo"
        with pytest.raises(GitHubAPIError) as exc_info:
            raise GitHubAPIError(error_msg)
        assert str(exc_info.value) == error_msg

    def test_api_error_inheritance_chain(self):
        """GitHubAPIError should inherit from Exception."""
        error = GitHubAPIError("Test")
        assert isinstance(error, Exception)


class TestGitHubNetworkException:
    """Test GitHubNetworkError exception."""

    def test_network_error_is_exception(self):
        """GitHubNetworkError should be an Exception."""
        assert issubclass(GitHubNetworkError, Exception)

    def test_network_error_can_be_raised(self):
        """GitHubNetworkError should be raisable."""
        with pytest.raises(GitHubNetworkError):
            raise GitHubNetworkError("Connection timeout")

    def test_network_error_message(self):
        """GitHubNetworkError should preserve message."""
        error_msg = "Network connection failed"
        with pytest.raises(GitHubNetworkError) as exc_info:
            raise GitHubNetworkError(error_msg)
        assert str(exc_info.value) == error_msg

    def test_network_error_inheritance_chain(self):
        """GitHubNetworkError should inherit from Exception."""
        error = GitHubNetworkError("Test")
        assert isinstance(error, Exception)


class TestGitHubRateLimitException:
    """Test GitHubRateLimitError exception."""

    def test_rate_limit_error_is_exception(self):
        """GitHubRateLimitError should be an Exception."""
        assert issubclass(GitHubRateLimitError, Exception)

    def test_rate_limit_error_can_be_raised(self):
        """GitHubRateLimitError should be raisable."""
        with pytest.raises(GitHubRateLimitError):
            raise GitHubRateLimitError("Rate limit exceeded")

    def test_rate_limit_error_message(self):
        """GitHubRateLimitError should preserve message."""
        error_msg = "API rate limit exceeded, retry after 1 hour"
        with pytest.raises(GitHubRateLimitError) as exc_info:
            raise GitHubRateLimitError(error_msg)
        assert str(exc_info.value) == error_msg

    def test_rate_limit_error_inheritance_chain(self):
        """GitHubRateLimitError should inherit from Exception."""
        error = GitHubRateLimitError("Test")
        assert isinstance(error, Exception)


class TestExceptionDistinction:
    """Test that exceptions can be distinguished from each other."""

    def test_exceptions_are_distinct_types(self):
        """All GitHub exceptions should be distinct types."""
        exceptions = [
            GitHubAuthError,
            GitHubAPIError,
            GitHubNetworkError,
            GitHubRateLimitError,
        ]
        # All should be different classes
        assert len(set(exceptions)) == len(exceptions)

    def test_catch_specific_auth_error(self):
        """Should be able to catch GitHubAuthError specifically."""
        try:
            raise GitHubAuthError("Auth failed")
        except GitHubAuthError as e:
            assert "Auth failed" in str(e)

    def test_catch_specific_api_error(self):
        """Should be able to catch GitHubAPIError specifically."""
        try:
            raise GitHubAPIError("API failed")
        except GitHubAPIError as e:
            assert "API failed" in str(e)

    def test_catch_specific_network_error(self):
        """Should be able to catch GitHubNetworkError specifically."""
        try:
            raise GitHubNetworkError("Network failed")
        except GitHubNetworkError as e:
            assert "Network failed" in str(e)

    def test_catch_specific_rate_limit_error(self):
        """Should be able to catch GitHubRateLimitError specifically."""
        try:
            raise GitHubRateLimitError("Rate limited")
        except GitHubRateLimitError as e:
            assert "Rate limited" in str(e)

    def test_auth_error_not_caught_as_network_error(self):
        """AuthError should not be caught as NetworkError."""
        with pytest.raises(GitHubAuthError):
            try:
                raise GitHubAuthError("Auth failed")
            except GitHubNetworkError:
                pytest.fail("AuthError caught as NetworkError")

    def test_multiple_exception_handlers(self):
        """Should support catching different exceptions separately."""
        errors_caught = []

        try:
            raise GitHubAuthError("Auth error")
        except GitHubAuthError:
            errors_caught.append("auth")
        except GitHubAPIError:
            errors_caught.append("api")

        try:
            raise GitHubRateLimitError("Rate limit")
        except GitHubRateLimitError:
            errors_caught.append("rate_limit")
        except GitHubNetworkError:
            errors_caught.append("network")

        assert errors_caught == ["auth", "rate_limit"]


class TestExceptionMessages:
    """Test exception message handling."""

    def test_empty_message(self):
        """Should handle empty exception messages."""
        error = GitHubAuthError("")
        assert str(error) == ""

    def test_multiline_message(self):
        """Should preserve multiline messages."""
        message = "Error 1\nError 2\nError 3"
        error = GitHubAPIError(message)
        assert str(error) == message

    def test_special_characters_in_message(self):
        """Should preserve special characters in messages."""
        message = "Error with 'quotes' and \"double quotes\" and \\ backslash"
        error = GitHubNetworkError(message)
        assert str(error) == message

    def test_unicode_in_message(self):
        """Should preserve unicode characters in messages."""
        message = "Error: 中文 العربية Ελληνικά"
        error = GitHubRateLimitError(message)
        assert str(error) == message
