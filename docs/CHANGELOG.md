# Changelog — Medidesk Integrator

Wszystkie znaczące zmiany w projekcie są dokumentowane w tym pliku.
Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

---

## [Unreleased] — branch `feat/medidesk-captcha-bridge`

### Dodane
- **Obsługa reCAPTCHA v3 Medideska w kliencie** — `submit_form_urlencoded()` przyjmuje opcjonalny `captcha_response` i wysyła go jako nagłówek `captcha-response` zgodnie ze specyfikacją Medideska (przywrócone z utraconej sesji).
- **Routing przez `webFormId`** — `resolve_submit_form_id()` pobiera `webFormId` z `GET /api/forms/{id}` i POST-uje na właściwy endpoint; POST bezpośrednio na `formTemplateId` UUID wywala u Medideska 500.
- **Endpoint `/api/submit/{form_id}`** akceptuje captcha-token z body (`captchaResponse`/`captchaToken`) lub z nagłówka `captcha-response`.
- **Demo `demo_contact.html`** integruje Google reCAPTCHA v3 client-side (`grecaptcha.execute`) — działa z przeglądarki end-to-end.
- **`recaptcha_bridge_url`** w configu — placeholder pod headless-captcha-bridge (Playwright) dla ścieżki server-to-server (FB webhook → Medidesk).

### Naprawione
- **Site-key reCAPTCHA** — wpisano poprawny klucz Medideska (`6Lfs81gh...PcBJ_`) ze specyfikacji API; poprzednia sesja wpisała inny klucz, przez co tokeny były odrzucane przy `siteverify` po stronie Medideska.

### Zmienione
- **URL produkcji** w docs/config/agents: `md-integrator-v1.onrender.com` → `md-integrator-old.onrender.com` (faktyczna nazwa serwisu w Render Dashboard).
- **Plan w `render.yaml`**: `free` → `starter` (zgodność z rzeczywistością).
- **`render.yaml` buildCommand** dodaje `playwright install --with-deps chromium` — wymagane przez nadchodzący captcha-bridge.

### Bezpieczeństwo
- Tag `przed_captcha_bridge_20260530` utworzony jako punkt powrotu przed pracami nad captcha.

### Znane problemy
- **FB webhook → Medidesk wciąż nie działa** — ścieżka server-to-server nie ma własnej przeglądarki, nie wygeneruje tokenu reCAPTCHA. Rozwiązanie w toku: Playwright captcha-bridge (kolejny commit na tej gałęzi).

---

## [2.0.0] — 2026-04-18

### Dodane
- **Silnik szablonów Jinja2** — zastąpił statyczne serwowanie plików HTML
- **Szablon bazowy `base.html`** — wspólny `<head>`, meta-dane, fonty, theme scripts
- **Katalog `app/static/`** — zamontowany jako `/static` via `StaticFiles`
- **`theme.css`** — zmienne CSS dla Light/Dark mode (`:root` + `[data-theme='dark']`)
- **`theme.js`** — synchroniczne wykrywanie motywu z `localStorage` / `prefers-color-scheme` (zapobiega FOIT)
- **Metadane aplikacji w `config.py`** — `app_name`, `app_version`, `app_author`, `app_icon_path`
- **Funkcja `render_template()`** — centralne renderowanie szablonów z automatycznym wstrzykiwaniem metadanych
- **Dokumentacja projektu** — `docs/README.md`, `docs/DEPLOYMENT.md`, `docs/CHANGELOG.md`

### Zmienione
- **Ikona aplikacji** przeniesiona z `app/MD_Integrator_V1.jpg` → `app/static/icon.jpg`
- **Pliki HTML** przeniesione z `app/*.html` → `app/templates/*.html`
- **Wszystkie endpointy HTML** zrefaktoryzowane z `HTMLResponse(read_text())` → `render_template()`

### Naprawione
- **Python 3.14 kompatybilność** — Jinja2 `LRUCache` crash fix via `cache_size=0`
- **Starlette >=0.28 kompatybilność** — `TemplateResponse` sygnatura z keyword args

### Bezpieczeństwo
- Tag `przed_refactoringiem` utworzony jako punkt powrotu

---

## [1.x] — do 2026-04-17

### Funkcjonalności
- Integracja Facebook Lead Ads → Medidesk (webhook-based)
- Panel admina z zarządzaniem użytkownikami i placówkami
- Setup wizard do konfiguracji mapowania pól
- Dashboard z KPI, listą leadów, podglądem integracji
- System zaproszeń do placówek (token links)
- AI-assisted field mapping (mapping_ai.py)
- Token expiry monitoring i alerting (Make.com webhooks)
- Szyfrowanie tokenów FB (Fernet)
- Admin login (hasło) + Facebook OAuth login
- Demo mode
- Facebook compliance pages (privacy, ToS, data deletion)
