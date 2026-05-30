from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
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


@app.get("/debug/captcha")
async def debug_captcha(form_id: str = "e8342a6a-b31a-4e2c-82be-146b73fe8457"):
    """Twarda diagnostyka bridge'a — zwraca realny błąd, nie None."""
    import traceback
    info: dict[str, Any] = {"site_key_set": bool(settings.recaptcha_site_key)}

    # 1. pakiet playwright
    try:
        from playwright.async_api import async_playwright
        info["playwright_import"] = "ok"
    except Exception as e:
        info["playwright_import"] = f"FAIL: {e!r}"
        return info

    # 2. czy binarka chromium istnieje
    try:
        pw = await async_playwright().start()
        try:
            exe = pw.chromium.executable_path
            import os
            info["chromium_path"] = exe
            info["chromium_exists"] = os.path.exists(exe)
        finally:
            await pw.stop()
    except Exception as e:
        info["chromium_check"] = f"FAIL: {e!r}"

    # 3. wymuś świeżą próbę — wołamy internale bezpośrednio, żeby
    #    wyjątki NIE były połykane (get_captcha_token zwraca None po cichu)
    try:
        import app.captcha_bridge as cb
        await cb.shutdown_bridge()
        cb._init_attempted = False
        bridge = cb.CaptchaBridge()
        await bridge.start()
        info["bridge_start"] = "ok"
        try:
            token = await bridge.get_token(form_id)
            info["token_len"] = len(token) if token else 0
            info["token_ok"] = bool(token)
        finally:
            await bridge.close()
    except Exception:
        info["token_error"] = traceback.format_exc()[-1800:]

    return info


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
