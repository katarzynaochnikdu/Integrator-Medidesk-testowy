"""Headless reCAPTCHA v3 bridge dla wywołań server-to-server do Medideska.

Dlaczego to istnieje
--------------------
Endpoint Medideska ``POST /api/forms/{webFormId}`` wymaga nagłówka
``captcha-response`` z tokenem Google reCAPTCHA v3 (zob. PDF spec, str. 3).
reCAPTCHA v3 generuje token w przeglądarce poprzez ``grecaptcha.execute()`` —
nie ma sposobu wytworzenia ważnego tokenu z czystego HTTP klienta.

Ścieżka **FB Lead Ads → webhook → Medidesk** jest server-to-server: nie ma
przeglądarki, nie ma użytkownika. Bez tokenu serwer Medideska zwraca HTTP 500
(powinien 401 zgodnie ze spec — to ich bug — ale faktycznie 500).

Ten moduł utrzymuje pojedynczy headless Chromium (Playwright) w procesie
aplikacji. Na żądanie otwiera stronę na ``app.medidesk.io`` (gdzie origin
zgadza się z whitelistą site-key'a Medideska) i wywołuje
``grecaptcha.execute()`` — zwraca świeży token, który następnie
``medidesk_client.submit_form_urlencoded`` wkłada do nagłówka żądania.

Cykl życia
----------
* **Lazy init**: bridge startuje przy pierwszym wywołaniu :func:`get_captcha_token`.
  Pozwala to aplikacji uruchomić się normalnie nawet gdy Playwright nie jest
  zainstalowany (np. środowisko dev lub stary deploy bez Chromium).
* **Singleton browser**: jedna instancja Chromium na cały proces. Per-request
  jest osobny ``BrowserContext`` (izolacja cookies / storage) — taniej niż
  startowanie nowego browsera za każdym razem.
* **Shutdown**: :func:`shutdown_bridge` woła się z FastAPI shutdown hook
  w ``main.py``.

Failure mode
-------------
Jeśli Playwright nie jest dostępny lub Chromium nie startuje — bridge milcząco
wraca ``None``. Wywołujący (medidesk_client) wtedy POST-uje bez tokenu i
dostaje od Medideska normalny błąd — żadnej cichej awarii.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Singleton bridge instance + jednorazowa flaga próby inicjalizacji.
# Druga flaga zapobiega spamowi w logach: gdy Playwright nie jest
# zainstalowany, log o tym pojawia się tylko RAZ, nie przy każdym leadzie.
_bridge: Optional["CaptchaBridge"] = None
_init_lock = asyncio.Lock()
_init_attempted: bool = False


async def get_captcha_token(form_id: str, action: str = "submit") -> Optional[str]:
    """Zwraca świeży token reCAPTCHA v3 lub ``None`` jeśli bridge niedostępny.

    Args:
        form_id: ``formTemplateId`` Medideska — używany do zbudowania URL
            strony bridge'owej (``https://app.medidesk.io/forms/{form_id}``).
            Możesz nadpisać URL globalnie przez ``MEDIDESK_RECAPTCHA_BRIDGE_URL``.
        action: Etykieta akcji reCAPTCHA v3 (przekazywana do
            ``grecaptcha.execute``). Domyślnie ``"submit"``.

    Returns:
        Token (str) lub ``None`` przy każdej awarii — wywołujący powinien
        traktować ``None`` jako „bez captchy" i pozwolić Medideskowi
        zwrócić własny błąd.
    """
    bridge = await _get_or_create_bridge()
    if bridge is None:
        return None
    try:
        return await bridge.get_token(form_id, action=action)
    except Exception:
        logger.warning("Captcha bridge: get_token raised", exc_info=True)
        return None


async def shutdown_bridge() -> None:
    """Zamyka headless browser przy shutdown aplikacji.

    Bezpieczne do wywołania nawet gdy bridge nigdy nie był zainicjalizowany.
    """
    global _bridge
    if _bridge is None:
        return
    try:
        await _bridge.close()
    except Exception:
        logger.warning("Captcha bridge: shutdown raised", exc_info=True)
    _bridge = None


async def _get_or_create_bridge() -> Optional["CaptchaBridge"]:
    global _bridge, _init_attempted
    if _bridge is not None:
        return _bridge
    async with _init_lock:
        if _bridge is not None:
            return _bridge
        if _init_attempted:
            # Wcześniejsza próba padła — nie próbujemy ponownie przy
            # każdym leadzie (spam logów + opóźnienie).
            return None
        _init_attempted = True
        try:
            from playwright.async_api import async_playwright  # noqa: F401
        except ImportError:
            logger.warning(
                "Captcha bridge: playwright NIE jest zainstalowany — bridge nieaktywny. "
                "Instalacja: pip install playwright && playwright install --with-deps chromium"
            )
            return None
        bridge = CaptchaBridge()
        try:
            await bridge.start()
        except Exception:
            logger.error("Captcha bridge: Chromium nie wystartował", exc_info=True)
            return None
        _bridge = bridge
        logger.info("Captcha bridge: gotowy (Chromium headless)")
        return _bridge


class CaptchaBridge:
    """Wrapper na trwałą instancję Playwright Chromium do generowania tokenów."""

    def __init__(self) -> None:
        self._pw = None
        self._browser = None

    async def start(self) -> None:
        from playwright.async_api import async_playwright

        self._pw = await async_playwright().start()
        # Flagi krytyczne dla kontenera Render:
        #   --no-sandbox — kontener nie ma capabilities do chrome-sandboxa,
        #   --disable-dev-shm-usage — /dev/shm w kontenerach Rendera jest mikre
        #     (~64 MB), Chromium domyślnie chce więcej → OOM przy renderowaniu,
        #   --disable-blink-features=AutomationControlled — usuwa heurystyczny
        #     marker „jestem automatyzacją" widziany przez bot-detektory.
        self._browser = await self._pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

    async def close(self) -> None:
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._pw is not None:
            await self._pw.stop()
            self._pw = None

    async def get_token(self, form_id: str, action: str = "submit") -> Optional[str]:
        """Otwiera stronę na domenie Medideska i woła ``grecaptcha.execute``.

        **Kluczowa właściwość**: dokument MUSI być na domenie znajdującej się
        na liście dozwolonych dla site-key'a w panelu reCAPTCHA. Site-key
        jest własnością Medideska; ich własna domena (``app.medidesk.io``)
        jest na liście — nasz ``*.onrender.com`` raczej nie. Dlatego
        domyślnym URL-em jest hostowana strona formularza Medideska.
        Jeśli wstrzykniemy skrypt grecaptcha na tej stronie, document.origin
        = ``app.medidesk.io`` i token przejdzie weryfikację po stronie
        ``siteverify`` u Medideska.
        """
        from app.config import settings

        if not settings.recaptcha_site_key:
            return None
        if self._browser is None:
            return None

        # Domyślny URL: hostowana strona formularza Medideska. Override przez
        # MEDIDESK_RECAPTCHA_BRIDGE_URL gdy klinika ma własną stronę z formą
        # (oraz własna domena jest na whiteliście site-key'a).
        bridge_url = (
            settings.recaptcha_bridge_url
            or f"https://app.medidesk.io/forms/{form_id}"
        )
        site_key = settings.recaptcha_site_key

        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        try:
            await page.goto(bridge_url, wait_until="domcontentloaded", timeout=20_000)
            # Strona Medideska to SPA — grecaptcha może być ładowane
            # asynchronicznie po hydratacji JS. Próbujemy krótko poczekać;
            # jeśli się nie pojawi, wstrzykujemy skrypt sami (origin
            # dokumentu i tak jest app.medidesk.io, Google to akceptuje).
            try:
                await page.wait_for_function(
                    "typeof grecaptcha !== 'undefined' "
                    "&& typeof grecaptcha.execute === 'function'",
                    timeout=5_000,
                )
            except Exception:
                logger.debug(
                    "Captcha bridge: grecaptcha nie załadowane przez SPA, wstrzykujemy ręcznie"
                )
                await page.add_script_tag(
                    url=f"https://www.google.com/recaptcha/api.js?render={site_key}"
                )
                await page.wait_for_function(
                    "typeof grecaptcha !== 'undefined' "
                    "&& typeof grecaptcha.execute === 'function'",
                    timeout=10_000,
                )

            # JS evaluator: czekamy aż grecaptcha będzie ready, potem execute.
            # Argumenty (siteKey, action) przekazujemy do evaluate() jako lista,
            # żeby nie sklejać stringów (escape-hell).
            token = await page.evaluate(
                """async ([siteKey, action]) => new Promise((resolve, reject) => {
                    grecaptcha.ready(() => {
                        grecaptcha.execute(siteKey, {action: action}).then(resolve, reject);
                    });
                })""",
                [site_key, action],
            )
            if isinstance(token, str) and token:
                logger.info(
                    "Captcha bridge: wygenerowano token (len=%d) dla form=%s",
                    len(token),
                    form_id,
                )
                return token
            return None
        finally:
            try:
                await context.close()
            except Exception:
                pass
