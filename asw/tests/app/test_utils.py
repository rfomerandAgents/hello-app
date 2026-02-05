"""Tests for ADW utility functions."""

import pytest
import sys

sys.path.insert(0, '..')
from asw.modules.utils import parse_cache_flag


class TestParseCacheFlag:
    """Test cache flag parsing from command line arguments."""

    @pytest.mark.parametrize("argv,expected_enabled,expected_cleaned", [
        # --cache enables caching
        (["script.py", "--cache", "431"], True, ["script.py", "431"]),
        # --no-cache disables caching
        (["script.py", "--no-cache", "431"], False, ["script.py", "431"]),
        # Default (no flag) disables caching
        (["script.py", "431", "adw-abc123"], False, ["script.py", "431", "adw-abc123"]),
        # Preserves other flags
        (["script.py", "431", "--skip-e2e", "--cache"], True, ["script.py", "431", "--skip-e2e"]),
        # Empty argv
        ([], False, []),
        # Only script name
        (["adw_plan_iso.py"], False, ["adw_plan_iso.py"]),
        # Flag at beginning
        (["--cache", "script.py", "431"], True, ["script.py", "431"]),
        # Flag at end
        (["script.py", "431", "--no-cache"], False, ["script.py", "431"]),
    ])
    def test_parse_cache_flag(self, argv, expected_enabled, expected_cleaned):
        """Parametrized test for cache flag parsing."""
        cache_enabled, cleaned = parse_cache_flag(argv)
        assert cache_enabled is expected_enabled
        assert cleaned == expected_cleaned

    def test_flag_removal_is_clean(self):
        """Flag should be completely removed, not leaving artifacts."""
        _, cleaned = parse_cache_flag(["adw_plan_iso.py", "431", "--cache"])
        assert "--cache" not in cleaned
        assert "--no-cache" not in cleaned
        assert "-cache" not in " ".join(cleaned)

    def test_original_argv_unchanged(self):
        """Original argv list should not be mutated."""
        original = ["script.py", "--cache", "431"]
        original_copy = original.copy()
        parse_cache_flag(original)
        assert original == original_copy

    def test_preserves_issue_number_and_adw_id(self):
        """Should preserve typical ADW arguments."""
        argv = ["adw_sdlc_iso.py", "431", "adw-abc12345", "--skip-e2e", "--cache"]
        cache_enabled, cleaned = parse_cache_flag(argv)
        assert cache_enabled is True
        assert "431" in cleaned
        assert "adw-abc12345" in cleaned
        assert "--skip-e2e" in cleaned
