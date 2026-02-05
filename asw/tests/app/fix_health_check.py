#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests"]
# ///

"""
Fix Webhook and Tunnel Health Check

Automatically fixes common webhook and Cloudflare tunnel issues:
- Starts webhook server if not running
- Starts Cloudflare tunnel if not running
- Verifies fixes by re-running health checks

Usage:
    uv run fix_health_check.py              # Interactive mode
    uv run fix_health_check.py --auto       # Auto-fix without prompting
    uv run fix_health_check.py --dry-run    # Show what would be fixed
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Get repo root directory
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
HEALTH_CHECK_SCRIPT = REPO_ROOT / "adws" / "adw_tests" / "webhook_tunnel_health_check.py"
WEBHOOK_SCRIPT = REPO_ROOT / "triggers" / "trigger_webhook.py"
TUNNEL_SCRIPT = REPO_ROOT / "scripts" / "expose_webhook.sh"

# Port configuration
WEBHOOK_PORT = 8001


class HealthCheckResults:
    """Container for health check results."""

    def __init__(self):
        self.port_listening = False
        self.local_health_ok = False
        self.cloudflared_running = False
        self.external_health_ok = False
        self.external_webhook_ok = False
        self.all_healthy = False
        self.raw_output = ""


def run_health_check() -> HealthCheckResults:
    """Run webhook health check and return parsed results."""
    print("\n" + "=" * 50)
    print("Running Health Check...")
    print("=" * 50 + "\n")

    results = HealthCheckResults()

    try:
        result = subprocess.run(
            ["uv", "run", str(HEALTH_CHECK_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )

        results.raw_output = result.stdout

        # Parse output to detect status
        output_lower = result.stdout.lower()

        # Check for specific status indicators
        if "port 8001 is listening" in output_lower:
            results.port_listening = True

        if "cloudflared running" in output_lower:
            results.cloudflared_running = True

        # Overall health is indicated by exit code
        results.all_healthy = (result.returncode == 0)

        # Check for successful external endpoints
        if "external health" in output_lower and "http 200" in output_lower:
            results.external_health_ok = True
        elif "external health" in output_lower and "http 405" in output_lower:
            # 405 is also OK for webhook endpoint (expects POST, not GET)
            results.external_webhook_ok = True

        # Print the actual output
        print(result.stdout)

        return results

    except subprocess.TimeoutExpired:
        print("Health check timed out after 30 seconds")
        return results
    except Exception as e:
        print(f"Error running health check: {e}")
        return results


def is_webhook_running() -> bool:
    """Check if webhook server is running on port 8001."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', WEBHOOK_PORT))
    sock.close()
    return result == 0


def is_cloudflared_running() -> bool:
    """Check if cloudflared process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "cloudflared"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def start_webhook_server(dry_run: bool = False) -> bool:
    """Start webhook server on port 8001."""
    print("\n[FIX] Starting webhook server on port 8001...")

    if dry_run:
        print("  [DRY-RUN] Would run: cd triggers && PORT=8001 uv run trigger_webhook.py &")
        return True

    try:
        # Create log directory
        log_dir = REPO_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)

        webhook_log = log_dir / "webhook_server.log"
        webhook_err = log_dir / "webhook_server.err"

        # Start webhook server in background
        with open(webhook_log, "w") as out, open(webhook_err, "w") as err:
            env = os.environ.copy()
            env["PORT"] = str(WEBHOOK_PORT)

            process = subprocess.Popen(
                ["uv", "run", str(WEBHOOK_SCRIPT)],
                cwd=str(REPO_ROOT / "triggers"),
                env=env,
                stdout=out,
                stderr=err,
                start_new_session=True  # Detach from parent
            )

        # Wait a moment for server to start
        time.sleep(2)

        # Verify it's running
        if is_webhook_running():
            print(f"  ✅ Webhook server started successfully (PID: {process.pid})")
            print(f"  Logs: {webhook_log}")
            return True
        else:
            print(f"  ❌ Webhook server may not have started correctly")
            print(f"  Check logs: {webhook_log} and {webhook_err}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to start webhook server: {e}")
        return False


def start_cloudflared_tunnel(dry_run: bool = False) -> bool:
    """Start Cloudflare tunnel."""
    print("\n[FIX] Starting Cloudflare tunnel...")

    if dry_run:
        print(f"  [DRY-RUN] Would run: {TUNNEL_SCRIPT} &")
        return True

    # Check if CLOUDFLARED_TUNNEL_TOKEN is set
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        print("  ❌ .env file not found")
        print("  Create .env file with CLOUDFLARED_TUNNEL_TOKEN")
        return False

    # Check if token exists in .env
    env_content = env_file.read_text()
    if "CLOUDFLARED_TUNNEL_TOKEN" not in env_content:
        print("  ❌ CLOUDFLARED_TUNNEL_TOKEN not found in .env")
        print("  Add CLOUDFLARED_TUNNEL_TOKEN to .env file")
        return False

    try:
        # Create log directory
        log_dir = REPO_ROOT / "logs"
        log_dir.mkdir(exist_ok=True)

        tunnel_log = log_dir / "cloudflared.log"
        tunnel_err = log_dir / "cloudflared.err"

        # Start tunnel in background
        with open(tunnel_log, "w") as out, open(tunnel_err, "w") as err:
            process = subprocess.Popen(
                ["bash", str(TUNNEL_SCRIPT)],
                cwd=str(REPO_ROOT),
                stdout=out,
                stderr=err,
                start_new_session=True  # Detach from parent
            )

        # Wait a moment for tunnel to start
        time.sleep(3)

        # Verify it's running
        if is_cloudflared_running():
            print(f"  ✅ Cloudflare tunnel started successfully (PID: {process.pid})")
            print(f"  Logs: {tunnel_log}")
            return True
        else:
            print(f"  ❌ Cloudflare tunnel may not have started correctly")
            print(f"  Check logs: {tunnel_log} and {tunnel_err}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to start Cloudflare tunnel: {e}")
        return False


def identify_fixes_needed(results: HealthCheckResults) -> list[str]:
    """Identify what fixes are needed based on health check results."""
    fixes = []

    if not results.port_listening:
        fixes.append("webhook_server")

    if not results.cloudflared_running:
        fixes.append("cloudflared_tunnel")

    return fixes


def apply_fixes(fixes: list[str], dry_run: bool = False, auto: bool = False) -> dict[str, bool]:
    """Apply the identified fixes."""
    results = {}

    if not fixes:
        print("\n✅ No fixes needed - system is healthy!")
        return results

    print(f"\n{'=' * 50}")
    print("Fixes Needed:")
    print(f"{'=' * 50}")

    for fix in fixes:
        if fix == "webhook_server":
            print("  • Start webhook server (port 8001)")
        elif fix == "cloudflared_tunnel":
            print("  • Start Cloudflare tunnel")

    if not auto and not dry_run:
        response = input("\nApply these fixes? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Aborted.")
            return results

    # Apply each fix
    if "webhook_server" in fixes:
        results["webhook_server"] = start_webhook_server(dry_run)

    if "cloudflared_tunnel" in fixes:
        results["cloudflared_tunnel"] = start_cloudflared_tunnel(dry_run)

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automatically fix webhook and tunnel health issues"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without actually fixing"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-fix without prompting for confirmation"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Webhook & Tunnel Auto-Fix")
    print("=" * 50)

    if args.dry_run:
        print("[DRY-RUN MODE - No changes will be made]")
    elif args.auto:
        print("[AUTO MODE - Fixes will be applied automatically]")

    # Step 1: Run initial health check
    print("\n[STEP 1] Running initial health check...")
    initial_results = run_health_check()

    if initial_results.all_healthy:
        print("\n" + "=" * 50)
        print("✅ System is already healthy - no fixes needed!")
        print("=" * 50)
        return 0

    # Step 2: Identify fixes needed
    print("\n[STEP 2] Identifying fixes needed...")
    fixes_needed = identify_fixes_needed(initial_results)

    if not fixes_needed:
        print("\n✅ No fixable issues detected.")
        print("\nSome issues may require manual intervention:")
        print("  • Check Cloudflare dashboard for tunnel status")
        print("  • Verify CLOUDFLARED_TUNNEL_TOKEN in .env")
        print("  • Check network connectivity")
        return 1

    # Step 3: Apply fixes
    print(f"\n[STEP 3] Applying fixes...")
    fix_results = apply_fixes(fixes_needed, dry_run=args.dry_run, auto=args.auto)

    if args.dry_run:
        print("\n[DRY-RUN] No changes were made.")
        return 0

    # Step 4: Re-run health check to verify
    if fix_results:
        print("\n[STEP 4] Verifying fixes...")
        time.sleep(2)  # Give services a moment to stabilize

        final_results = run_health_check()

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)

        print("\nFixes Applied:")
        for fix, success in fix_results.items():
            status = "✅" if success else "❌"
            fix_name = fix.replace("_", " ").title()
            print(f"  {status} {fix_name}")

        print(f"\nFinal Status: {'✅ HEALTHY' if final_results.all_healthy else '⚠️ ISSUES REMAIN'}")

        if not final_results.all_healthy:
            print("\nRemaining issues may require manual intervention:")
            if not final_results.cloudflared_running:
                print("  • Check CLOUDFLARED_TUNNEL_TOKEN in .env")
                print("  • Verify Cloudflare tunnel configuration")
            if not final_results.external_health_ok:
                print("  • Check Cloudflare dashboard")
                print("  • Verify DNS configuration")

        return 0 if final_results.all_healthy else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
