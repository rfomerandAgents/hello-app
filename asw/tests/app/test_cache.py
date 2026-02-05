"""Tests for ADW caching module."""

import pytest
import sys
import time

sys.path.insert(0, '..')
from asw.modules.cache import create_fingerprint, CacheEntry


class TestCreateFingerprint:
    """Test deterministic cache fingerprint generation."""

    def test_deterministic_same_inputs(self):
        """Identical inputs must always produce identical fingerprints."""
        prompt = "Add Lucy to the jenny gallery with her biography"
        fp1 = create_fingerprint(prompt, "sonnet")
        fp2 = create_fingerprint(prompt, "sonnet")
        assert fp1 == fp2

    def test_different_prompts_different_fingerprints(self):
        """Different prompts must produce different fingerprints."""
        fp1 = create_fingerprint("Add Penny to gallery", "sonnet")
        fp2 = create_fingerprint("Add Mercury to gallery", "sonnet")
        assert fp1 != fp2

    def test_model_affects_fingerprint(self):
        """Same prompt with different model should differ."""
        prompt = "Update breeding status for Pink Lady"
        fp_sonnet = create_fingerprint(prompt, "sonnet")
        fp_opus = create_fingerprint(prompt, "opus")
        assert fp_sonnet != fp_opus

    def test_working_dir_affects_fingerprint(self):
        """Working directory context should affect fingerprint."""
        prompt = "Run tests"
        fp1 = create_fingerprint(prompt, "sonnet", working_dir="/.worktrees/adw-abc123")
        fp2 = create_fingerprint(prompt, "sonnet", working_dir="/.worktrees/adw-xyz789")
        assert fp1 != fp2

    def test_fingerprint_format(self):
        """Fingerprint should be valid 32-char hex (MD5)."""
        fp = create_fingerprint("Test lineage tree for Curry Ann", "sonnet")
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)

    def test_none_optional_params_consistent(self):
        """None and omitted optional params should match."""
        fp1 = create_fingerprint("test", "sonnet", working_dir=None, slash_command=None)
        fp2 = create_fingerprint("test", "sonnet")
        assert fp1 == fp2

    def test_slash_command_affects_fingerprint(self):
        """Slash command should affect fingerprint."""
        prompt = "Implement feature"
        fp1 = create_fingerprint(prompt, "sonnet", slash_command="/feature")
        fp2 = create_fingerprint(prompt, "sonnet", slash_command="/chore")
        assert fp1 != fp2

    def test_long_prompt_deterministic(self):
        """Long prompts should still produce deterministic fingerprints."""
        long_prompt = "Update the image gallery " * 100
        fp1 = create_fingerprint(long_prompt, "sonnet")
        fp2 = create_fingerprint(long_prompt, "sonnet")
        assert fp1 == fp2
        assert len(fp1) == 32  # Still 32 chars regardless of input length
