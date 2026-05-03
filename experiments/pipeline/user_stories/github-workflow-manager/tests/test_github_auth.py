"""Tests for GitHub authentication management."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from src.auth.github_auth import GitHubAuthManager
from src.exceptions import GitHubAuthError


class TestGitHubAuthManagerTokenResolution:
    """Test token resolution with three-tier priority."""

    def test_explicit_token_has_highest_priority(self):
        """Explicit token should be returned without checking env or file."""
        auth = GitHubAuthManager()
        explicit_token = "ghp_explicit_token_12345678901234567890"

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(auth, "_load_token_from_file", return_value=None):
                with patch.object(auth, "_prompt_for_token", return_value=None):
                    token = auth.get_token(explicit_token=explicit_token)
                    assert token == explicit_token

    def test_env_var_used_when_no_explicit_token(self):
        """GITHUB_TOKEN env var should be used when explicit token not provided."""
        auth = GitHubAuthManager()
        env_token = "ghp_env_token_12345678901234567890123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": env_token}):
            with patch.object(auth, "_load_token_from_file", return_value=None):
                with patch.object(auth, "_prompt_for_token", return_value=None):
                    token = auth.get_token(explicit_token=None)
                    assert token == env_token

    def test_file_token_used_when_no_env_var(self):
        """Token from secrets/.env should be used when env var not set."""
        auth = GitHubAuthManager()
        file_token = "ghp_file_token_12345678901234567890123"

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(auth, "_load_token_from_file", return_value=file_token):
                with patch.object(auth, "_prompt_for_token", return_value=None):
                    token = auth.get_token(explicit_token=None)
                    assert token == file_token

    def test_user_prompt_used_when_no_other_sources(self):
        """User prompt should be used as fallback when all other sources missing."""
        auth = GitHubAuthManager()
        prompt_token = "ghp_prompt_token_12345678901234567890"

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(auth, "_load_token_from_file", return_value=None):
                with patch.object(auth, "_prompt_for_token", return_value=prompt_token):
                    token = auth.get_token(explicit_token=None)
                    assert token == prompt_token

    def test_auth_error_when_no_token_available(self):
        """GitHubAuthError should be raised when no token can be resolved."""
        auth = GitHubAuthManager()

        with patch.dict(os.environ, {}, clear=True):
            with patch.object(auth, "_load_token_from_file", return_value=None):
                with patch.object(auth, "_prompt_for_token", return_value=None):
                    with pytest.raises(GitHubAuthError) as exc_info:
                        auth.get_token(explicit_token=None)
                    assert "No GitHub token found" in str(exc_info.value)


class TestGitHubAuthManagerFileLoading:
    """Test token loading from secrets/.env file."""

    def test_load_token_from_file_success(self):
        """Token should be loaded from secrets/.env file."""
        auth = GitHubAuthManager()
        file_content = "# Comment\nGITHUB_TOKEN=ghp_file_token_12345678901234567890\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                token = auth._load_token_from_file()
                assert token == "ghp_file_token_12345678901234567890"

    def test_load_token_with_whitespace(self):
        """Token should be stripped of leading/trailing whitespace."""
        auth = GitHubAuthManager()
        file_content = "  GITHUB_TOKEN=  ghp_token_with_spaces_1234567890  \n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                token = auth._load_token_from_file()
                assert token == "ghp_token_with_spaces_1234567890"

    def test_file_not_exists_returns_none(self):
        """None should be returned if secrets/.env doesn't exist."""
        auth = GitHubAuthManager()

        with patch("pathlib.Path.exists", return_value=False):
            token = auth._load_token_from_file()
            assert token is None

    def test_file_read_error_returns_none(self):
        """None should be returned on file read error."""
        auth = GitHubAuthManager()

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Read failed")):
                token = auth._load_token_from_file()
                assert token is None

    def test_skip_comment_lines(self):
        """Comment lines starting with # should be skipped."""
        auth = GitHubAuthManager()
        file_content = "# This is a comment\n# GITHUB_TOKEN=ghp_fake_token\nGITHUB_TOKEN=ghp_real_token_12345678901\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                token = auth._load_token_from_file()
                assert token == "ghp_real_token_12345678901"

    def test_skip_empty_lines(self):
        """Empty lines should be skipped."""
        auth = GitHubAuthManager()
        file_content = "\n\nGITHUB_TOKEN=ghp_token_12345678901234567890\n\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                token = auth._load_token_from_file()
                assert token == "ghp_token_12345678901234567890"

    def test_only_first_token_returned(self):
        """Only the first token should be returned."""
        auth = GitHubAuthManager()
        file_content = "GITHUB_TOKEN=ghp_first_token_12345678901\nGITHUB_TOKEN=ghp_second_token_1234567890\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                token = auth._load_token_from_file()
                assert token == "ghp_first_token_12345678901"

    def test_no_token_in_file_returns_none(self):
        """None should be returned if file has no GITHUB_TOKEN line."""
        auth = GitHubAuthManager()
        file_content = "# Just comments\nOTHER_VAR=value\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            with patch("pathlib.Path.exists", return_value=True):
                token = auth._load_token_from_file()
                assert token is None


class TestGitHubAuthManagerUserPrompt:
    """Test user prompt for token input."""

    def test_prompt_returns_token(self):
        """User-entered token should be returned."""
        auth = GitHubAuthManager()
        user_token = "ghp_user_token_12345678901234567890"

        with patch("src.auth.github_auth.getpass", return_value=user_token):
            token = auth._prompt_for_token()
            assert token == user_token

    def test_prompt_returns_none_on_keyboard_interrupt(self):
        """None should be returned if user cancels with Ctrl+C."""
        auth = GitHubAuthManager()

        with patch("src.auth.github_auth.getpass", side_effect=KeyboardInterrupt):
            token = auth._prompt_for_token()
            assert token is None

    def test_prompt_returns_none_on_eof_error(self):
        """None should be returned if EOF is encountered."""
        auth = GitHubAuthManager()

        with patch("src.auth.github_auth.getpass", side_effect=EOFError):
            token = auth._prompt_for_token()
            assert token is None

    def test_empty_input_returns_none(self):
        """None should be returned for empty input."""
        auth = GitHubAuthManager()

        with patch("src.auth.github_auth.getpass", return_value=""):
            token = auth._prompt_for_token()
            assert token is None


class TestGitHubAuthManagerTokenValidation:
    """Test token format validation."""

    @pytest.mark.parametrize("token", [
        "ghp_abc123def456789012345678901234567890",
        "ghu_abc123def456789012345678901234567890",
        "ghs_abc123def456789012345678901234567890",
        "gho_abc123def456789012345678901234567890",
    ])
    def test_valid_token_formats(self, token):
        """All GitHub token prefixes should be accepted."""
        auth = GitHubAuthManager()
        assert auth.validate_token(token) is True

    @pytest.mark.parametrize("invalid_token", [
        "invalid_token",
        "ghp_short",
        "xyz_abc123def456789012345678901234567890",
        "GHP_abc123def456789012345678901234567890",
        "",
        "ghp_",
    ])
    def test_invalid_token_formats(self, invalid_token):
        """Invalid token formats should be rejected."""
        auth = GitHubAuthManager()
        assert auth.validate_token(invalid_token) is False

    def test_invalid_token_none(self):
        """None should not be a valid token."""
        auth = GitHubAuthManager()
        with pytest.raises(TypeError):
            auth.validate_token(None)

    def test_token_validation_boundary_length(self):
        """Token with exactly 36 characters after prefix should be valid."""
        auth = GitHubAuthManager()
        # ghp_ (4) + 36 chars = 40 total
        token = "ghp_" + "a" * 36
        assert auth.validate_token(token) is True

    def test_token_validation_max_length(self):
        """Token with 255 total characters should be valid."""
        auth = GitHubAuthManager()
        token = "ghp_" + "a" * 251  # 255 total
        assert auth.validate_token(token) is True

    def test_token_validation_alphanumeric_and_underscore(self):
        """Alphanumeric characters and underscores should be allowed in token."""
        auth = GitHubAuthManager()
        # Token with letters, numbers, but underscore is internal to the token body
        token = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
        assert auth.validate_token(token) is True


class TestGitHubAuthManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_secrets_file_path_constant(self):
        """SECRETS_FILE_PATH should be 'secrets/.env'."""
        auth = GitHubAuthManager()
        assert auth.SECRETS_FILE_PATH == "secrets/.env"

    def test_token_env_var_constant(self):
        """TOKEN_ENV_VAR should be 'GITHUB_TOKEN'."""
        auth = GitHubAuthManager()
        assert auth.TOKEN_ENV_VAR == "GITHUB_TOKEN"

    def test_explicit_token_none_uses_other_sources(self):
        """Explicitly passing None should use other token sources."""
        auth = GitHubAuthManager()
        env_token = "ghp_env_token_12345678901234567890123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": env_token}):
            token = auth.get_token(explicit_token=None)
            assert token == env_token

    def test_explicit_empty_string_token_uses_other_sources(self):
        """Empty string explicit token should be treated as not provided."""
        auth = GitHubAuthManager()
        env_token = "ghp_env_token_12345678901234567890123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": env_token}):
            # Empty string is falsy, so it should use other sources
            token = auth.get_token(explicit_token="")
            assert token == env_token

    def test_multiple_tokens_env_overrides_file(self):
        """Env var should take priority over file when both present."""
        auth = GitHubAuthManager()
        env_token = "ghp_env_token_12345678901234567890123"
        file_token = "ghp_file_token_12345678901234567890"

        with patch.dict(os.environ, {"GITHUB_TOKEN": env_token}):
            with patch.object(auth, "_load_token_from_file", return_value=file_token):
                token = auth.get_token(explicit_token=None)
                assert token == env_token
