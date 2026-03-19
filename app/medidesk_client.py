from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Minimalny PNG 1×1 px (prawidłowy plik) – spełnia wymaganie pola ATTACHMENTS, jeśli formularz wymaga „Dodaj-zdjęcie”
_MIN_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)
MINIMAL_PNG_BYTES = base64.b64decode(_MIN_PNG_B64)

ALLOWED_ATTACHMENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text",
    "text/plain",
}

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB


@dataclass
class MedideskResult:
    success: bool
    status_code: int
    body: dict[str, Any] | None = None
    raw_text: str | None = None


async def submit_form(
    payload: dict[str, Any],
    captcha_token: str,
) -> MedideskResult:
    """POST the mapped payload to the Medidesk forms endpoint."""

    headers = {
        "Content-Type": "application/json",
        "captcha-response": captcha_token,
    }

    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        try:
            resp = await client.post(
                settings.medidesk_form_url,
                json=payload,
                headers=headers,
            )
        except httpx.TimeoutException:
            logger.warning("Medidesk request timed out")
            return MedideskResult(success=False, status_code=504)
        except httpx.HTTPError as exc:
            logger.error("Medidesk HTTP error: %s", exc)
            return MedideskResult(success=False, status_code=502)

    body = None
    raw_text = (resp.text or "")[:8000] if resp.text else None
    try:
        body = resp.json()
    except Exception:
        pass

    if resp.status_code != 200:
        preview = (resp.text or "")[:1200]
        # INFO żeby w logach Rendera (domyślnie INFO) było widać treść bez podnoszenia poziomu
        logger.info(
            "Medidesk POST form status=%s json=%s text_preview=%s",
            resp.status_code,
            body,
            preview,
        )
        if resp.status_code == 500 and isinstance(body, dict):
            if body.get("error") == "Internal Server Error" and "web-form" in str(
                body.get("path", "")
            ):
                logger.info(
                    "Wskazówka: Medidesk często zwraca ten generyczny 500 przy "
                    "braku/wygasłym/nieakceptowanym tokenie reCAPTCHA (zamiast 401). "
                    "Dodaj domenę Rendera (np. *.onrender.com) w Google reCAPTCHA Admin dla tego site key "
                    "i użyj świeżego tokenu z /demo/contact."
                )

    return MedideskResult(
        success=resp.status_code == 200,
        status_code=resp.status_code,
        body=body,
        raw_text=raw_text,
    )


async def verify_recaptcha_google_token(
    token: str,
    secret: str,
) -> tuple[bool, dict[str, Any]]:
    """Wywołanie Google siteverify – to samo co Medidesk robi po swojej stronie.

    Zwraca (True, data) jeśli success==True, inaczej (False, data).
    """
    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        try:
            resp = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={"secret": secret, "response": token},
            )
        except httpx.HTTPError as exc:
            logger.error("Google siteverify HTTP error: %s", exc)
            return False, {"error": "siteverify_transport"}

    try:
        data = resp.json()
    except Exception:
        return False, {"error": "siteverify_invalid_json", "text": (resp.text or "")[:200]}

    ok = data.get("success") is True
    return ok, data


async def get_placeholder_attachment_id(captcha_token: str | None = None) -> str | None:
    """Upload minimalnego PNG dla wymaganego pola „Dodaj-zdjęcie”."""
    return await upload_attachment(
        MINIMAL_PNG_BYTES, "placeholder.png", captcha_token=captcha_token
    )


async def upload_attachment(
    file_bytes: bytes,
    filename: str,
    *,
    captcha_token: str | None = None,
) -> str | None:
    """Upload a single file to the Medidesk attachments endpoint.

    Returns the attachment UUID on success, or None on failure.
    Niektóre konfiguracje Medidesk mogą wymagać tego samego tokenu co przy submit formularza.
    """

    headers: dict[str, str] = {}
    if captcha_token:
        headers["captcha-response"] = captcha_token

    async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
        try:
            resp = await client.post(
                settings.medidesk_attachments_url,
                files={"file": (filename, file_bytes)},
                headers=headers or None,
            )
        except httpx.HTTPError as exc:
            logger.error("Attachment upload failed: %s", exc)
            return None

    if resp.status_code != 200:
        logger.info(
            "Medidesk attachment upload status=%d captcha_header=%s body=%s",
            resp.status_code,
            bool(captcha_token),
            (resp.text or "")[:800],
        )
        return None

    data = resp.json()
    return data.get("id")
