"""Pluggable provider tokenów reCAPTCHA v3 dla wysyłki do Medideska.

Przełącznik trybu przez ``MEDIDESK_CAPTCHA_MODE``:
  * ``solver``  — zewnętrzny serwis (CapSolver) generuje token z wysokim score
                  (residential IP + wygrzane profile). Jedyna metoda, która
                  realnie przechodzi dla ścieżki server-to-server (FB webhook).
  * ``bridge``  — headless Playwright otwiera app.medidesk.io i woła
                  grecaptcha.execute. Działa, ale na datacenter IP Rendera
                  dostaje niski score → Medidesk zwraca 401.
  * ``none``    — bez tokenu (POST poleci bez nagłówka captcha-response).

Wywołujący (``medidesk_client.submit_form_urlencoded``) woła
:func:`get_captcha_token` tylko gdy sam nie dostał tokenu (np. z przeglądarki
na demo page, gdzie token generuje grecaptcha po stronie usera).
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CAPSOLVER_BASE = "https://api.capsolver.com"


async def get_captcha_token(
    form_id: str,
    action: str | None = None,
    enterprise: bool | None = None,
) -> str | None:
    """Zwraca token reCAPTCHA v3 wg skonfigurowanego trybu lub ``None``.

    ``action`` / ``enterprise`` pozwalają nadpisać ustawienia (do testów
    przez /debug/send) — gdy None, biorą wartość z configu.
    """
    mode = (settings.captcha_mode or "none").strip().lower()
    if mode == "solver":
        return await _solve_capsolver(form_id, action=action, enterprise=enterprise)
    if mode == "bridge":
        try:
            from app.captcha_bridge import get_captcha_token as bridge_token
            return await bridge_token(form_id)
        except Exception:
            logger.warning("captcha bridge failed for form=%s", form_id, exc_info=True)
            return None
    return None


def _website_url(form_id: str) -> str:
    """URL strony, dla której solver generuje token.

    Musi być domeną na whiteliście site-key'a Medideska — ich własna
    ``app.medidesk.io`` jest. Override przez MEDIDESK_RECAPTCHA_BRIDGE_URL.
    """
    return settings.recaptcha_bridge_url or f"https://app.medidesk.io/forms/{form_id}"


async def _solve_capsolver(
    form_id: str,
    action: str | None = None,
    enterprise: bool | None = None,
) -> str | None:
    """CapSolver: createTask → poll getTaskResult → gRecaptchaResponse.

    Wymaga ``MEDIDESK_SOLVER_CAPTCHA_API_KEY`` oraz
    ``MEDIDESK_RECAPTCHA_SITE_KEY``. Akcja/próg z configu (lub override).
    ``enterprise=True`` używa typu Enterprise (inny endpoint weryfikacji
    po stronie Medideska — token classic nie przejdzie do Enterprise).
    """
    if not settings.solver_captcha_api_key:
        logger.warning("CapSolver: brak MEDIDESK_SOLVER_CAPTCHA_API_KEY")
        return None
    if not settings.recaptcha_site_key:
        logger.warning("CapSolver: brak MEDIDESK_RECAPTCHA_SITE_KEY")
        return None

    use_action = action if action is not None else (settings.captcha_action or "submit")
    use_enterprise = settings.captcha_enterprise if enterprise is None else enterprise
    task_type = "ReCaptchaV3EnterpriseTask" if use_enterprise else "ReCaptchaV3TaskProxyLess"

    task = {
        "type": task_type,
        "websiteURL": _website_url(form_id),
        "websiteKey": settings.recaptcha_site_key,
        "pageAction": use_action,
        "minScore": settings.captcha_min_score,
    }
    create_payload = {"clientKey": settings.solver_captcha_api_key, "task": task}

    async with httpx.AsyncClient(timeout=settings.captcha_timeout) as client:
        try:
            r = await client.post(f"{CAPSOLVER_BASE}/createTask", json=create_payload)
            data = r.json()
        except Exception:
            logger.error("CapSolver createTask error", exc_info=True)
            return None

        if data.get("errorId"):
            logger.warning(
                "CapSolver createTask odrzucony: %s / %s",
                data.get("errorCode"), data.get("errorDescription"),
            )
            return None

        task_id = data.get("taskId")
        if not task_id:
            logger.warning("CapSolver: brak taskId w odpowiedzi")
            return None

        # Polling — CapSolver v3 zwykle 5–20s. Czekamy do captcha_timeout.
        deadline_loops = max(1, int(settings.captcha_timeout // 3))
        for _ in range(deadline_loops):
            await asyncio.sleep(3)
            try:
                rr = await client.post(
                    f"{CAPSOLVER_BASE}/getTaskResult",
                    json={"clientKey": settings.solver_captcha_api_key, "taskId": task_id},
                )
                res = rr.json()
            except Exception:
                logger.error("CapSolver getTaskResult error", exc_info=True)
                return None

            if res.get("errorId"):
                logger.warning(
                    "CapSolver getTaskResult błąd: %s / %s",
                    res.get("errorCode"), res.get("errorDescription"),
                )
                return None

            status = res.get("status")
            if status == "ready":
                token = (res.get("solution") or {}).get("gRecaptchaResponse")
                if token:
                    logger.info("CapSolver: token gotowy (len=%d) form=%s", len(token), form_id)
                    return token
                logger.warning("CapSolver: status ready ale brak gRecaptchaResponse")
                return None
            # status == "processing" → pętla dalej

    logger.warning("CapSolver: przekroczono czas oczekiwania na token form=%s", form_id)
    return None
