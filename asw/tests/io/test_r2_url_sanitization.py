#!/usr/bin/env -S uv run
# /// script
# dependencies = ["boto3>=1.26.0"]
# ///

"""Unit tests for R2Uploader URL sanitization and construction."""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asw.modules.r2_uploader import R2Uploader


def setup_logger() -> logging.Logger:
    """Set up a simple logger for tests."""
    logger = logging.getLogger("test_r2_url_sanitization")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def test_domain_without_protocol():
    """Test that domain without protocol works correctly."""
    print("\n1️⃣ Testing domain without protocol prefix...")

    logger = setup_logger()

    with patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "test_account",
        "CLOUDFLARE_R2_ACCESS_KEY_ID": "test_key",
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test_secret",
        "CLOUDFLARE_R2_BUCKET_NAME": "test_bucket",
        "CLOUDFLARE_R2_PUBLIC_DOMAIN": "example.com"
    }):
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            uploader = R2Uploader(logger)

            assert uploader.public_domain == "example.com", \
                f"Expected 'example.com', got '{uploader.public_domain}'"

            # Mock file existence and upload to test URL construction
            with patch('os.path.exists', return_value=True):
                url = uploader.upload_file("test.png", "test/ipe_validate.png")
                expected = "https://example.com/ipe_validate/ipe_validate.png"

                assert url == expected, \
                    f"Expected '{expected}', got '{url}'"

                print(f"   ✅ Domain 'example.com' → URL '{url}'")

    return True


def test_domain_with_https_protocol():
    """Test that domain with https:// protocol is sanitized correctly."""
    print("\n2️⃣ Testing domain with https:// protocol prefix...")

    logger = setup_logger()

    with patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "test_account",
        "CLOUDFLARE_R2_ACCESS_KEY_ID": "test_key",
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test_secret",
        "CLOUDFLARE_R2_BUCKET_NAME": "test_bucket",
        "CLOUDFLARE_R2_PUBLIC_DOMAIN": "https://example.com"
    }):
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            uploader = R2Uploader(logger)

            assert uploader.public_domain == "example.com", \
                f"Expected 'example.com', got '{uploader.public_domain}'"

            # Mock file existence and upload to test URL construction
            with patch('os.path.exists', return_value=True):
                url = uploader.upload_file("test.png", "test/ipe_validate.png")
                expected = "https://example.com/ipe_validate/ipe_validate.png"

                assert url == expected, \
                    f"Expected '{expected}', got '{url}'"
                assert url.count("https://") == 1, \
                    f"URL should have exactly one 'https://', got: {url}"

                print(f"   ✅ Domain 'https://example.com' → URL '{url}'")

    return True


def test_domain_with_http_protocol():
    """Test that domain with http:// protocol is sanitized and converted to https."""
    print("\n3️⃣ Testing domain with http:// protocol prefix...")

    logger = setup_logger()

    with patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "test_account",
        "CLOUDFLARE_R2_ACCESS_KEY_ID": "test_key",
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test_secret",
        "CLOUDFLARE_R2_BUCKET_NAME": "test_bucket",
        "CLOUDFLARE_R2_PUBLIC_DOMAIN": "http://example.com"
    }):
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            uploader = R2Uploader(logger)

            assert uploader.public_domain == "example.com", \
                f"Expected 'example.com', got '{uploader.public_domain}'"

            # Mock file existence and upload to test URL construction
            with patch('os.path.exists', return_value=True):
                url = uploader.upload_file("test.png", "test/ipe_validate.png")
                expected = "https://example.com/ipe_validate/ipe_validate.png"

                assert url == expected, \
                    f"Expected '{expected}', got '{url}'"
                assert url.startswith("https://"), \
                    f"URL should use https://, got: {url}"
                assert "http://http" not in url, \
                    f"URL should not have duplicate protocols, got: {url}"

                print(f"   ✅ Domain 'http://example.com' → URL '{url}'")

    return True


def test_default_domain():
    """Test that default domain is used when env var is not set."""
    print("\n4️⃣ Testing default domain (no env var)...")

    logger = setup_logger()

    with patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "test_account",
        "CLOUDFLARE_R2_ACCESS_KEY_ID": "test_key",
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test_secret",
        "CLOUDFLARE_R2_BUCKET_NAME": "test_bucket",
    }, clear=False):
        # Remove the public domain env var if it exists
        if "CLOUDFLARE_R2_PUBLIC_DOMAIN" in os.environ:
            del os.environ["CLOUDFLARE_R2_PUBLIC_DOMAIN"]

        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            uploader = R2Uploader(logger)

            expected_domain = "tac-public-imgs.iddagents.com"
            assert uploader.public_domain == expected_domain, \
                f"Expected '{expected_domain}', got '{uploader.public_domain}'"

            # Mock file existence and upload to test URL construction
            with patch('os.path.exists', return_value=True):
                url = uploader.upload_file("test.png", "test/ipe_validate.png")
                expected = f"https://{expected_domain}/ipe_validate/ipe_validate.png"

                assert url == expected, \
                    f"Expected '{expected}', got '{url}'"

                print(f"   ✅ Default domain '{expected_domain}' → URL '{url}'")

    return True


def test_cloudflare_r2_domain_with_https():
    """Test the actual bug scenario from issue #26."""
    print("\n5️⃣ Testing bug scenario from issue #26...")

    logger = setup_logger()

    # This is the exact domain from the bug report
    buggy_domain = "https://6309f6ec5f448b47a2f03ad3e710f450.r2.cloudflarestorage.com"

    with patch.dict(os.environ, {
        "CLOUDFLARE_ACCOUNT_ID": "test_account",
        "CLOUDFLARE_R2_ACCESS_KEY_ID": "test_key",
        "CLOUDFLARE_R2_SECRET_ACCESS_KEY": "test_secret",
        "CLOUDFLARE_R2_BUCKET_NAME": "test_bucket",
        "CLOUDFLARE_R2_PUBLIC_DOMAIN": buggy_domain
    }):
        with patch('boto3.client') as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client

            uploader = R2Uploader(logger)

            sanitized = "6309f6ec5f448b47a2f03ad3e710f450.r2.cloudflarestorage.com"
            assert uploader.public_domain == sanitized, \
                f"Expected '{sanitized}', got '{uploader.public_domain}'"

            # Mock file existence and upload to test URL construction
            with patch('os.path.exists', return_value=True):
                url = uploader.upload_file("test.png", "adw/1ce486c4/review/01_app_running_homepage.png")
                expected = f"https://{sanitized}/adw/1ce486c4/review/01_app_running_homepage.png"

                assert url == expected, \
                    f"Expected '{expected}', got '{url}'"

                # Ensure no duplicate https://
                assert url.count("https://") == 1, \
                    f"URL should have exactly one 'https://', got: {url}"
                assert "https://https://" not in url, \
                    f"URL should not have 'https://https://', got: {url}"

                print(f"   ✅ Bug domain sanitized correctly")
                print(f"      Input:  '{buggy_domain}'")
                print(f"      Output: '{url}'")

    return True


def main():
    """Run all tests."""
    print("R2Uploader URL Sanitization Tests")
    print("=" * 70)

    all_tests_passed = True

    # Run all test functions
    test_functions = [
        test_domain_without_protocol,
        test_domain_with_https_protocol,
        test_domain_with_http_protocol,
        test_default_domain,
        test_cloudflare_r2_domain_with_https,
    ]

    for test_func in test_functions:
        try:
            if not test_func():
                all_tests_passed = False
        except AssertionError as e:
            print(f"   ❌ FAILED: {e}")
            all_tests_passed = False
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            all_tests_passed = False

    print("\n" + "=" * 70)
    if all_tests_passed:
        print("✅ All URL sanitization tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
