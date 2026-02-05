#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest"]
# ///

"""Unit tests for GitHub retry logic."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.github import is_retryable_github_error


def test_network_error_is_retryable():
    """Test that network errors are classified as retryable."""
    # The exact error from issue 210
    error = "error connecting to api.github.com\ncheck your internet connection"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is True
    assert category == "network"


def test_connection_refused_is_retryable():
    """Test that connection refused errors are retryable."""
    error = "connection refused"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is True
    assert category == "network"


def test_dns_error_is_retryable():
    """Test that DNS resolution errors are retryable."""
    error = "could not resolve host: api.github.com"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is True
    assert category == "network"


def test_timeout_is_retryable():
    """Test that timeout errors are retryable."""
    error = "request timed out"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is True
    assert category == "timeout"


def test_rate_limit_is_retryable():
    """Test that rate limit errors are retryable."""
    error = "API rate limit exceeded for user"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is True
    assert category == "rate_limit"


def test_server_error_is_retryable():
    """Test that 5xx errors are retryable."""
    error = "received 502 bad gateway"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is True
    assert category == "server"


def test_auth_error_not_retryable():
    """Test that authentication errors are not retryable."""
    error = "authentication failed (401)"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is False
    assert category == "auth"


def test_not_found_not_retryable():
    """Test that 404 errors are not retryable."""
    error = "issue not found (404)"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is False
    assert category == "not_found"


def test_unknown_error_not_retryable():
    """Test that unknown errors default to not retryable."""
    error = "some random error"
    is_retryable, category = is_retryable_github_error(error)
    assert is_retryable is False
    assert category == "unknown"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
