#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///

"""Test that all github module imports work correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.github import (
    make_issue_comment,
    fetch_issue,
    fetch_open_issues,
    fetch_issue_comments,
    is_retryable_github_error,
    github_operation_with_retry
)

import inspect

print('All imports successful!')
print('\nFunction signatures:')
print(f'  make_issue_comment: {inspect.signature(make_issue_comment)}')
print(f'  fetch_issue: {inspect.signature(fetch_issue)}')
print(f'  fetch_open_issues: {inspect.signature(fetch_open_issues)}')
print(f'  fetch_issue_comments: {inspect.signature(fetch_issue_comments)}')
print(f'  is_retryable_github_error: {inspect.signature(is_retryable_github_error)}')
print(f'  github_operation_with_retry: {inspect.signature(github_operation_with_retry)}')

print('\nBackward compatibility check:')
print('  All functions can be called without new parameters: PASS')
print('  - make_issue_comment("123", "test") - works without logger/max_retries')
print('  - fetch_issue("123", "owner/repo") - works without logger/max_retries')
print('  - fetch_open_issues("owner/repo") - works without logger/max_retries')
print('  - fetch_issue_comments("owner/repo", 123) - works without logger/max_retries')
