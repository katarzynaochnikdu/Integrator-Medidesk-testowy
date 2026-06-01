import hmac
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.medidesk_client import fetch_form_definition, submit_form_urlencoded

import logging

logger = logging.getLogger(__name__)

app = FastAPI(docs_url=None, redoc_url=None)


@app.on_event("shutdown")
async def shutdown_captcha_bridge():
    try:
        from app.captcha_bridge import shutdown_bridge
        await shutdown_bridge()
    except Exception:
        logger.warning("captcha bridge shutdown failed", exc_info=True)

_env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    cache_size=0,  # Python 3.14 compat — LRUCache crash fix
)


@app.get("/demo/contact", include_in_schema=False)
async def demo_contact(form_id: str = "e8342a6a-b31a-4e2c-82be-146b73fe8457"):
    html = _env.get_template("demo_contact.html").render(
        recaptcha_site_key=settings.recaptcha_site_key,
        default_form_id=form_id,
    )
    return HTMLResponse(html)


async def require_debug_token(request: Request) -> None:
    """Gate dla /debug/*: shared token w env (MEDIDESK_DEBUG_TOKEN).

    Akceptuje X-Debug-Token (preferowane) lub query param ?token=.
    Fail-closed: brak skonfigurowanego tokenu → 503 (nie da się trafić w domyślny).
    """
    configured = settings.debug_token
    if not configured:
        raise HTTPException(status_code=503, detail="Debug endpoints disabled (MEDIDESK_DEBUG_TOKEN not set)")
    provided = request.headers.get("X-Debug-Token") or request.query_params.get("token") or ""
    if not provided or not hmac.compare_digest(provided, configured):
        raise HTTPException(status_code=401, detail="Invalid debug token")


@app.get("/debug/captcha", dependencies=[Depends(require_debug_token)])
async def debug_captcha(form_id: str = "e8342a6a-b31a-4e2c-82be-146b73fe8457"):
    """Diagnostyka providera captcha — generuje token wg aktualnego trybu."""
    import time
    import traceback

    info: dict[str, Any] = {
        "mode": settings.captcha_mode,
        "site_key_set": bool(settings.recaptcha_site_key),
        "api_key_set": bool(settings.solver_captcha_api_key),
        "action": settings.captcha_action,
        "min_score": settings.captcha_min_score,
        "website_url": settings.recaptcha_bridge_url or f"https://app.medidesk.io/forms/{form_id}",
    }
    t0 = time.time()
    try:
        from app.captcha_provider import get_captcha_token
        token = await get_captcha_token(form_id)
        info["elapsed_s"] = round(time.time() - t0, 1)
        info["token_ok"] = bool(token)
        info["token_len"] = len(token) if token else 0
        if token:
            info["token_preview"] = token[:40] + "…"
    except Exception:
        info["elapsed_s"] = round(time.time() - t0, 1)
        info["error"] = traceback.format_exc()[-1800:]

    return info


@app.get("/debug/send", dependencies=[Depends(require_debug_token)])
async def debug_send(
    form_id: str = "e8342a6a-b31a-4e2c-82be-146b73fe8457",
    action: str | None = None,
    enterprise: bool = False,
    min_score: float | None = None,
    site_key: str | None = None,
):
    """Pełny przepływ end-to-end: token → POST do Medideska → realny status.

    Parametry URL nadpisują config bez redeployu, np.:
      /debug/send?action=submit
      /debug/send?action=
      /debug/send?enterprise=true
    Pozwala szybko przelecieć kandydatów na `action` i tryb Enterprise.
    """
    import time

    out: dict[str, Any] = {
        "form_id": form_id,
        "action_used": settings.captcha_action if action is None else action,
        "enterprise": enterprise,
    }

    # 1. token z solvera (z override action/enterprise)
    t0 = time.time()
    try:
        from app.captcha_provider import get_captcha_token
        token = await get_captcha_token(form_id, action=action, enterprise=enterprise, min_score=min_score, site_key=site_key)
    except Exception as e:
        out["stage"] = "token"
        out["error"] = repr(e)
        return out
    out["token_ok"] = bool(token)
    out["token_s"] = round(time.time() - t0, 1)
    out["header_used"] = settings.captcha_header
    if not token:
        out["stage"] = "token"
        out["note"] = "solver nie zwrócił tokenu"
        try:
            import app.captcha_provider as cp
            out["solver_error"] = cp.last_solver_error
        except Exception:
            pass
        return out

    # 2. POST do Medideska z tym tokenem + syntetyczne dane wg typów pól
    defn = await fetch_form_definition(form_id)
    if not defn:
        out["stage"] = "form"
        out["error"] = "GET form definition failed"
        return out

    fake = {"TEXT_FIELD": "Jan Testowy", "TEXT_AREA": "Test", "EMAIL": "jan.test@example.com",
            "PHONE": "+48500600700", "CHECKBOX": "true"}
    fields_values: dict[str, str] = {}
    for f in defn.fields:
        if f.field_type == "SELECT" and f.options:
            fields_values[f.field_id] = f.options[0]
        else:
            fields_values[f.field_id] = fake.get(f.field_type, "test")

    result = await submit_form_urlencoded(
        form_id, fields_values,
        site_domain="app.medidesk.io", site_url=f"/forms/{form_id}",
        captcha_response=token,
    )
    out["stage"] = "done"
    out["medidesk_status"] = result.status_code
    out["medidesk_ok"] = result.success
    out["medidesk_body"] = (result.raw_text or "")[:500]
    return out


@app.get("/api/forms/{form_id}/fields")
async def get_form_fields(form_id: str) -> dict[str, Any]:
    defn = await fetch_form_definition(form_id)
    if not defn:
        return JSONResponse(status_code=404, content={"error": "Formularz nie znaleziony"})
    return {
        "form_id": form_id,
        "web_form_id": defn.web_form_id,
        "form_name": defn.name,
        "fields": [
            {
                "fieldId": f.field_id,
                "type": f.field_type,
                "required": f.required,
                "name": f.name,
                "options": f.options,
            }
            for f in defn.fields
        ],
    }


@app.post("/api/submit/{form_id}")
async def submit_to_medidesk(form_id: str, request: Request):
    body = await request.json()
    site_domain = body.pop("siteDomain", None)
    site_url = body.pop("siteUrl", None)
    captcha_response = (
        body.pop("captchaResponse", None)
        or body.pop("captchaToken", None)
        or request.headers.get("captcha-response")
    )
    fields_values = {k: str(v) for k, v in body.items() if v is not None}

    result = await submit_form_urlencoded(
        form_id, fields_values, site_domain, site_url,
        captcha_response=captcha_response,
    )

    if result.success:
        return {"status": "ok"}
    return JSONResponse(
        status_code=502,
        content={"error": f"Medidesk HTTP {result.status_code}", "detail": result.raw_text},
    )
