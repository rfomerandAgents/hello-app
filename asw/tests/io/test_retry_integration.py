#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "pytest"]
# ///

"""Integration test for GitHub retry logic."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.github import github_operation_with_retry
import time


def test_retry_succeeds_on_transient_failure():
    """Test that retry logic succeeds after transient failures."""
    attempts = []

    def flaky_operation():
        attempts.append(len(attempts) + 1)
        if len(attempts) < 2:
            # Fail first time with a retryable error
            raise RuntimeError("error connecting to api.github.com")
        # Succeed on second attempt
        return "success"

    result = github_operation_with_retry(
        operation=flaky_operation,
        operation_name="test operation",
        max_retries=3,
        base_delay=0.1,  # Short delay for testing
    )

    assert result == "success"
    assert len(attempts) == 2  # Should have tried twice


def test_retry_fails_immediately_on_non_retryable_error():
    """Test that non-retryable errors fail immediately."""
    attempts = []

    def auth_error_operation():
        attempts.append(len(attempts) + 1)
        raise RuntimeError("authentication failed (401)")

    try:
        github_operation_with_retry(
            operation=auth_error_operation,
            operation_name="test operation",
            max_retries=3,
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "authentication" in str(e)
        assert len(attempts) == 1  # Should not have retried


def test_retry_exhausts_retries():
    """Test that retry logic exhausts all retries before failing."""
    attempts = []

    def always_fails():
        attempts.append(len(attempts) + 1)
        raise RuntimeError("error connecting to api.github.com")

    try:
        github_operation_with_retry(
            operation=always_fails,
            operation_name="test operation",
            max_retries=2,
            base_delay=0.05,
        )
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "error connecting" in str(e)
        assert len(attempts) == 3  # Initial + 2 retries


def test_exponential_backoff():
    """Test that delays increase exponentially."""
    delays = []
    attempts = []

    def timing_operation():
        if attempts:
            # Record time since last attempt
            delays.append(time.time() - attempts[-1])
        attempts.append(time.time())
        if len(attempts) < 3:
            raise RuntimeError("error connecting to api.github.com")
        return "success"

    github_operation_with_retry(
        operation=timing_operation,
        operation_name="test operation",
        max_retries=3,
        base_delay=0.1,
    )

    # Check that delays roughly follow exponential pattern
    # First retry: ~0.1s, Second retry: ~0.2s
    assert len(delays) == 2
    assert 0.08 < delays[0] < 0.15  # ~0.1s with tolerance
    assert 0.18 < delays[1] < 0.25  # ~0.2s with tolerance


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
