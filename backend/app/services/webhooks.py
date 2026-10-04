import hmac
import hashlib
import json
import logging
import socket
import ipaddress
import asyncio
from urllib.parse import urlparse
from typing import Optional, Tuple
import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.models import Webhook, WebhookDelivery, AppSetting
from app.core.config import settings

logger = logging.getLogger("chainnetra.webhooks")

# Blocked IP Networks for SSRF Protection
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    # IPv6 ranges
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8")
]

class SSRFValidationError(Exception):
    pass

def validate_webhook_url(url: str, db: Optional[Session] = None) -> Tuple[str, str]:
    if not url or not isinstance(url, str):
        raise SSRFValidationError("Webhook URL must be a non-empty string")
    
    parsed = urlparse(url.strip())
    is_live = settings.CHAINNETRA_MODE.upper() == "LIVE"

    if is_live:
        if parsed.scheme != "https":
            raise SSRFValidationError("Webhook URL must use HTTPS in LIVE mode")
    else:
        if parsed.scheme not in ("http", "https"):
            raise SSRFValidationError("Webhook URL must use HTTP or HTTPS")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("Invalid hostname in webhook URL")

    # Check optional admin domain allowlist from AppSetting
    if db:
        allowlist_setting = db.query(AppSetting).filter(AppSetting.key == "WEBHOOK_ALLOWED_DOMAINS").first()
        if allowlist_setting and allowlist_setting.value.strip():
            allowed_domains = [d.strip().lower() for d in allowlist_setting.value.split(",") if d.strip()]
            if not any(hostname.lower() == d or hostname.lower().endswith("." + d) for d in allowed_domains):
                raise SSRFValidationError(f"Hostname '{hostname}' is not in the allowed webhook domains list")

    # DNS Resolution and IP check (anti-SSRF / anti-rebinding)
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as e:
        raise SSRFValidationError(f"Failed to resolve hostname '{hostname}': {e}")

    for family, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        ip_obj = ipaddress.ip_address(ip_str)

        for blocked_net in BLOCKED_IP_NETWORKS:
            if ip_obj in blocked_net:
                raise SSRFValidationError(f"Access to private/reserved IP {ip_str} ({hostname}) is forbidden")

    return url.strip(), hostname

class WebhookService:
    @staticmethod
    async def dispatch_event(db: Session, event_type: str, payload: dict):
        webhooks = db.query(Webhook).filter(Webhook.is_active == True).all()
        for wh in webhooks:
            events_list = json.loads(wh.events or "[]")
            if event_type != "test_ping" and event_type not in events_list and "all" not in events_list:
                continue

            # Validate target URL against SSRF
            try:
                target_url, _ = validate_webhook_url(wh.target_url, db=db)
            except SSRFValidationError as e:
                logger.error(f"Blocked webhook dispatch for id {wh.id} due to SSRF validation: {e}")
                delivery = WebhookDelivery(
                    webhook_id=wh.id,
                    event_type=event_type,
                    payload=json.dumps(payload),
                    status_code=0,
                    response_body=f"SSRF blocked: {str(e)}",
                    latency_ms=0,
                    success=False,
                    attempt_count=1
                )
                db.add(delivery)
                db.commit()
                continue

            timestamp_str = datetime.now(timezone.utc).isoformat()
            body_json = json.dumps({
                "event": event_type,
                "timestamp": timestamp_str,
                "data": payload
            }, sort_keys=True)

            # HMAC signature over timestamp + body
            to_sign = f"{timestamp_str}.{body_json}"
            signature = hmac.new(
                wh.secret.encode('utf-8'),
                to_sign.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "X-ChainNetra-Signature": signature,
                "X-ChainNetra-Timestamp": timestamp_str,
                "X-ChainNetra-Event": event_type,
                "User-Agent": "ChainNetra-Forensic-Webhook/1.0"
            }

            # Exponential backoff retry (up to 3 attempts)
            max_attempts = 3
            success = False
            status_code = 0
            response_text = ""
            total_latency = 0.0

            for attempt in range(1, max_attempts + 1):
                start_t = datetime.now(timezone.utc)
                try:
                    async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
                        resp = await client.post(target_url, content=body_json, headers=headers)
                        status_code = resp.status_code
                        response_text = resp.text[:500]
                        total_latency = (datetime.now(timezone.utc) - start_t).total_seconds() * 1000.0

                        if 200 <= resp.status_code < 300:
                            success = True
                            break
                        else:
                            success = False
                except Exception as ex:
                    status_code = 0
                    response_text = f"Connection error: {str(ex)}"
                    success = False
                    total_latency = (datetime.now(timezone.utc) - start_t).total_seconds() * 1000.0

                if not success and attempt < max_attempts:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

            delivery = WebhookDelivery(
                webhook_id=wh.id,
                event_type=event_type,
                payload=body_json,
                status_code=status_code,
                response_body=response_text,
                latency_ms=round(total_latency, 1),
                success=success,
                attempt_count=attempt
            )
            db.add(delivery)
            db.commit()
