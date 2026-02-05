# Health Check - Webhook & Cloudflare Tunnel

Perform a comprehensive health check of the webhook server and Cloudflare tunnel.

## Checks Performed

1. **Local Webhook Port (8001)**: Verifies the webhook server is listening
2. **Local Health Endpoint**: Tests http://localhost:8001/health
3. **Cloudflared Process**: Confirms cloudflared tunnel is running
4. **External Health**: Tests https://somenetwork.org/health via tunnel
5. **External Webhook**: Confirms https://somenetwork.org/gh-webhook is reachable

## Run

!`uv run asw/app/adw_tests/webhook_tunnel_health_check.py`

Report the results of the health check.

## Troubleshooting

### If Webhook Not Running

Start the webhook server:
```bash
cd triggers && PORT=8001 uv run trigger_webhook.py
```

Or with logging:
```bash
./scripts/start_webhook_with_logging.sh
```

### If Tunnel Not Running

Start the Cloudflare tunnel:
```bash
./scripts/expose_webhook.sh
```

### If External Checks Fail

1. Check Cloudflare dashboard for tunnel status
2. Verify `CLOUDFLARED_TUNNEL_TOKEN` is set in `.env`
3. Check if tunnel configuration matches somenetwork.org domain
