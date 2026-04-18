"""Token health check and email alerting via Make.com webhook."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def debug_fb_token(access_token: str) -> dict[str, Any]:
    """Check token validity and expiration via FB Graph API debug_token."""
    url = f"https://graph.facebook.com/{settings.fb_graph_version}/debug_token"
    params = {
        "input_token": access_token,
        "access_token": f"{settings.fb_app_id}|{settings.fb_app_secret}",
    }
    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        logger.error("FB debug_token failed: %s", resp.text[:500])
        return {"valid": False, "error": resp.text[:200]}

    data = resp.json().get("data", {})
    is_valid = data.get("is_valid", False)
    expires_at = data.get("expires_at", 0)

    if expires_at == 0:
        # Token never expires (page tokens)
        return {"valid": is_valid, "expires_at": None, "days_remaining": None, "never_expires": True}

    expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    days_remaining = (expires_dt - now).days

    return {
        "valid": is_valid,
        "expires_at": expires_dt.isoformat(),
        "days_remaining": days_remaining,
        "never_expires": False,
    }


async def check_all_tokens() -> list[dict[str, Any]]:
    """Check all integration tokens and return status for each."""
    from app.integrations_store import get_all_integrations

    if not settings.fb_app_id or not settings.fb_app_secret:
        logger.warning("FB app credentials not set — skipping token check")
        return []

    integrations = get_all_integrations()
    results = []
    for i in integrations:
        if not i.active:
            continue
        try:
            status = await debug_fb_token(i.fb_page_token)
            status["integration_id"] = i.id
            status["fb_page_name"] = i.fb_page_name
            status["fb_form_name"] = i.fb_form_name
            results.append(status)
        except Exception:
            logger.error("Failed to check token for integration %s", i.id, exc_info=True)
            results.append({
                "integration_id": i.id,
                "fb_page_name": i.fb_page_name,
                "valid": False,
                "error": "Check failed",
            })
    return results


async def send_alert_email(subject: str, body: str) -> bool:
    """Send an alert email via Make.com webhook."""
    if not settings.make_webhook_send_email:
        logger.warning("Make webhook URL not configured — cannot send alert email")
        return False

    payload = {
        "to": settings.alert_email,
        "subject": subject,
        "body": body,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(settings.make_webhook_send_email, json=payload)
        if resp.status_code in (200, 201, 202):
            logger.info("Alert email sent: %s", subject)
            return True
        else:
            logger.error("Make webhook failed: %s %s", resp.status_code, resp.text[:200])
            return False
    except Exception:
        logger.error("Failed to send alert email", exc_info=True)
        return False


async def check_and_alert() -> None:
    """Check all tokens and send alerts for expiring ones."""
    results = await check_all_tokens()
    expiring = []
    for r in results:
        if r.get("never_expires"):
            continue
        days = r.get("days_remaining")
        if days is not None and days < settings.token_expiry_warn_days:
            expiring.append(r)
        if not r.get("valid"):
            expiring.append(r)

    if not expiring:
        logger.info("All tokens OK")
        return

    # Build alert message
    lines = ["⚠️ Integracja Leadów do Medidesk — Token Alert\n"]
    for r in expiring:
        name = r.get("fb_page_name", "?")
        days = r.get("days_remaining", "?")
        valid = "✅" if r.get("valid") else "❌"
        lines.append(f"• {name}: {valid} valid, {days} dni do wygaśnięcia")

    body = "\n".join(lines)
    logger.warning("Token alert:\n%s", body)

    if settings.alert_email and settings.make_webhook_send_email:
        await send_alert_email("⚠️ Token FB wygasa!", body)
