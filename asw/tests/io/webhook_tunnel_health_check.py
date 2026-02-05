#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests"]
# ///

"""
Webhook and Tunnel Health Check

Checks:
1. Local webhook running on port 8001
2. Local health endpoint responding
3. Cloudflare tunnel accessible externally
4. External webhook endpoint reachable
"""

import socket
import subprocess
import sys

try:
    import requests
except ImportError:
    requests = None

LOCAL_WEBHOOK_PORT = 8001
LOCAL_HEALTH_URL = f"http://localhost:{LOCAL_WEBHOOK_PORT}/health"
EXTERNAL_HEALTH_URL = "https://somenetwork.org/health"
EXTERNAL_WEBHOOK_URL = "https://somenetwork.org/gh-webhook"


def check_port_listening(port: int) -> tuple[bool, str]:
    """Check if a port is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    if result == 0:
        return True, f"Port {port} is listening"
    return False, f"Port {port} is NOT listening"


def check_url(url: str, timeout: int = 5) -> tuple[bool, str, int]:
    """Check if URL is accessible."""
    if requests is None:
        # Fallback to curl
        try:
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "--connect-timeout", str(timeout), url],
                capture_output=True, text=True, timeout=timeout+2
            )
            status_code = int(result.stdout.strip())
            success = 200 <= status_code < 500
            return success, f"HTTP {status_code}", status_code
        except Exception as e:
            return False, str(e), 0
    else:
        try:
            resp = requests.get(url, timeout=timeout)
            success = 200 <= resp.status_code < 500
            return success, f"HTTP {resp.status_code}", resp.status_code
        except requests.exceptions.Timeout:
            return False, "Timeout", 0
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {e}", 0
        except Exception as e:
            return False, str(e), 0


def check_cloudflared_running() -> tuple[bool, str]:
    """Check if cloudflared process is running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "cloudflared"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            return True, f"cloudflared running (PIDs: {', '.join(pids)})"
        return False, "cloudflared NOT running"
    except Exception as e:
        return False, f"Error checking cloudflared: {e}"


def main():
    print("🏥 Webhook & Tunnel Health Check\n")
    print("=" * 50)

    all_healthy = True

    # Check 1: Port 8001 listening
    print("\n📡 Check 1: Local Webhook Port")
    port_ok, port_msg = check_port_listening(LOCAL_WEBHOOK_PORT)
    print(f"   {'✅' if port_ok else '❌'} {port_msg}")
    all_healthy = all_healthy and port_ok

    # Check 2: Local health endpoint
    print("\n🔍 Check 2: Local Health Endpoint")
    if port_ok:
        local_ok, local_msg, _ = check_url(LOCAL_HEALTH_URL)
        print(f"   {'✅' if local_ok else '❌'} {LOCAL_HEALTH_URL}: {local_msg}")
        all_healthy = all_healthy and local_ok
    else:
        print(f"   ⏭️  Skipped (port not listening)")

    # Check 3: cloudflared process
    print("\n🌐 Check 3: Cloudflared Process")
    cf_ok, cf_msg = check_cloudflared_running()
    print(f"   {'✅' if cf_ok else '❌'} {cf_msg}")
    all_healthy = all_healthy and cf_ok

    # Check 4: External health via tunnel
    print("\n🔗 Check 4: External Health (via Cloudflare Tunnel)")
    ext_ok, ext_msg, _ = check_url(EXTERNAL_HEALTH_URL, timeout=10)
    print(f"   {'✅' if ext_ok else '❌'} {EXTERNAL_HEALTH_URL}: {ext_msg}")
    all_healthy = all_healthy and ext_ok

    # Check 5: External webhook endpoint (expect 405 Method Not Allowed for GET)
    print("\n📮 Check 5: External Webhook Endpoint")
    wh_ok, wh_msg, wh_code = check_url(EXTERNAL_WEBHOOK_URL, timeout=10)
    # 405 Method Not Allowed is expected for GET (endpoint only accepts POST)
    if wh_code == 405:
        print(f"   ✅ {EXTERNAL_WEBHOOK_URL}: HTTP 405 (expected - POST only)")
    elif wh_ok:
        print(f"   ✅ {EXTERNAL_WEBHOOK_URL}: {wh_msg}")
    else:
        print(f"   ❌ {EXTERNAL_WEBHOOK_URL}: {wh_msg}")
        all_healthy = False

    # Summary
    print("\n" + "=" * 50)
    if all_healthy:
        print("✅ OVERALL STATUS: HEALTHY")
        print("   Webhook is running on port 8001")
        print("   Cloudflare tunnel is serving https://somenetwork.org/gh-webhook")
    else:
        print("❌ OVERALL STATUS: UNHEALTHY")
        print("\n📋 Troubleshooting:")
        if not port_ok:
            print("   • Start webhook: cd triggers && PORT=8001 uv run trigger_webhook.py")
        if not cf_ok:
            print("   • Start tunnel: ./scripts/expose_webhook.sh")
        if not ext_ok:
            print("   • Check Cloudflare dashboard for tunnel status")
            print("   • Verify CLOUDFLARED_TUNNEL_TOKEN in .env")

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
