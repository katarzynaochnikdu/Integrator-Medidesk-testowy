# Medidesk Integrator — Dokumentacja Projektu

> **Wersja**: 2.0.0  
> **Autor**: Aga - Marketing  
> **Kontakt**: adminzoho@medidesk.com  
> **Repozytorium**: https://github.com/katarzynaochnikdu/Integrator-Medidesk-testowy  
> **Produkcja**: https://md-integrator-old.onrender.com

---

## Opis

Medidesk Integrator to aplikacja webowa (FastAPI) łącząca **Facebook Lead Ads** z systemem **Medidesk**. Leady z formularzy reklamowych na Facebooku są automatycznie przesyłane do Medidesk w czasie rzeczywistym za pomocą webhooków.

## Architektura

```
┌──────────────┐     webhook      ┌───────────────────┐     POST     ┌──────────┐
│  Facebook    │ ──────────────►  │  MD Integrator    │ ──────────►  │ Medidesk │
│  Lead Ads   │                  │  (FastAPI/Render)  │              │   API    │
└──────────────┘                  └───────────────────┘              └──────────┘
                                         │
                                    SQLite DB
                                  (integracje, leady,
                                   użytkownicy, sesje)
```

### Stos technologiczny

| Warstwa | Technologia |
|---|---|
| Backend | FastAPI + Uvicorn |
| Szablony HTML | Jinja2 + `base.html` layout |
| Pliki statyczne | `app/static/` via `StaticFiles` |
| Baza danych | SQLite (plik `medidesk.db`) |
|Auth | Facebook OAuth 2.0 + sesje cookie |
| Szyfrowanie tokenów | Fernet (cryptography) |
| Hosting | Render.com (Free tier, Frankfurt) |
| CI/CD | Auto-deploy z `main` branch GitHub |

### Struktura katalogów

```
Integrator/
├── app/
│   ├── main.py              # Główny router FastAPI + endpointy
│   ├── config.py             # Konfiguracja (pydantic-settings, env vars)
│   ├── db.py                 # SQLite schema + migracje
│   ├── fb_auth.py            # Facebook OAuth flow
│   ├── fb_client.py          # Facebook Graph API client
│   ├── webhook.py            # FB webhook handler (leady)
│   ├── medidesk_client.py    # Medidesk API client
│   ├── integrations_store.py # CRUD integracji
│   ├── users_store.py        # CRUD użytkowników + role
│   ├── mapping_ai.py         # AI-assisted field mapping
│   ├── lead_tracker.py       # Log leadów (events table)
│   ├── alerting.py           # Token expiry monitoring
│   ├── templates/            # Szablony Jinja2
│   │   ├── base.html         # Layout bazowy (head, meta, scripts)
│   │   ├── landing.html      # Strona logowania
│   │   ├── dashboard.html    # Panel zarządzania
│   │   ├── setup_wizard.html # Kreator integracji
│   │   ├── admin_login.html  # Login admina
│   │   ├── privacy.html      # Polityka prywatności (FB compliance)
│   │   ├── tos.html          # Regulamin (FB compliance)
│   │   ├── data_deletion.html # Instrukcja usunięcia danych
│   │   └── demo_contact.html # Demo page
│   └── static/               # Zasoby statyczne
│       ├── icon.jpg           # Ikona aplikacji
│       ├── theme.css          # Zmienne CSS (Light/Dark mode)
│       └── theme.js           # FOIT prevention (sync theme detection)
├── render.yaml               # Konfiguracja Render.com
├── requirements.txt          # Zależności Python
└── docs/                     # Dokumentacja
    ├── README.md              # ← Ten plik
    ├── DEPLOYMENT.md          # Wdrożenie i gotchas
    └── CHANGELOG.md           # Historia zmian
```

## Konfiguracja

Wszystkie zmienne środowiskowe mają prefix `MEDIDESK_` (zdefiniowane w `app/config.py`).

### Zmienne obowiązkowe (produkcja)

| Zmienna | Opis |
|---|---|
| `MEDIDESK_FB_APP_ID` | ID aplikacji Facebook |
| `MEDIDESK_FB_APP_SECRET` | Secret aplikacji Facebook |
| `MEDIDESK_FB_REDIRECT_URI` | Callback URL OAuth (np. `https://domena/auth/facebook/callback`) |
| `MEDIDESK_ENCRYPTION_KEY` | Klucz Fernet do szyfrowania tokenów FB |
| `MEDIDESK_FB_SESSION_SECRET` | Secret do podpisywania cookies sesji |
| `MEDIDESK_ADMIN_PASSWORD` | Hasło admina |
| `MEDIDESK_ADMIN_EMAIL` | Email konta administratora |
| `MEDIDESK_DATA_DIR` | Ścieżka do danych na Renderze (`/data`) |

### Zmienne opcjonalne

| Zmienna | Domyślna | Opis |
|---|---|---|
| `MEDIDESK_DEMO_PAGE_ENABLED` | `false` | Włącza stronę demo |
| `MEDIDESK_CORS_ORIGINS` | `""` | Dozwolone originy CORS (przecinkami) |
| `MEDIDESK_HTTP_TIMEOUT` | `15.0` | Timeout HTTP w sekundach |
| `MEDIDESK_MAKE_WEBHOOK_SEND_EMAIL` | `""` | Webhook Make.com do alertów |
| `MEDIDESK_TOKEN_EXPIRY_WARN_DAYS` | `14` | Alert X dni przed wygaśnięciem tokenu |
| `MEDIDESK_DEBUG_TOKEN` | `""` | Shared token chroniący `/debug/*`. Pusty = endpoint zwraca 503 (fail-closed). |

### Captcha — tryby i ENV (Medidesk reCAPTCHA v3 Enterprise)

Endpoint `POST /api/forms/{webFormId}` Medideska jest chroniony przez reCAPTCHA v3 (Enterprise). Klient (`app/medidesk_client.py` + `app/captcha_provider.py`) wstawia token jako nagłówek `enterprise-recaptcha-response`. Przełącznik trybu: `MEDIDESK_CAPTCHA_MODE`.

| Tryb | Kiedy | Wymaga |
|---|---|---|
| `solver` (**oficjalny / produkcyjny**) | Server-to-server (FB webhook → Medidesk). Token z CapSolver — residential IP, wysoki score. | `MEDIDESK_SOLVER_CAPTCHA_API_KEY`, `MEDIDESK_RECAPTCHA_SITE_KEY` |
| `bridge` (fallback) | Headless Playwright/Chromium na `app.medidesk.io` — wywołuje `grecaptcha.execute()`. Na datacenter IP Rendera score zwykle za niski. | `playwright` + Chromium (build step) |
| `none` | Captcha tymczasowo wyłączona po stronie Medideska albo lokalny dev. | — |

**Konfiguracja (default w `app/config.py`)**

| Zmienna | Default | Opis |
|---|---|---|
| `MEDIDESK_CAPTCHA_MODE` | `solver` | `solver` \| `bridge` \| `none` |
| `MEDIDESK_CAPTCHA_HEADER` | `enterprise-recaptcha-response` | Nazwa nagłówka z tokenem |
| `MEDIDESK_SOLVER_CAPTCHA_API_KEY` | — | clientKey CapSolver (https://capsolver.com) |
| `MEDIDESK_RECAPTCHA_SITE_KEY` | — | Site-key Medideska: `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk` |
| `MEDIDESK_CAPTCHA_ACTION` | `submit` | `pageAction` reCAPTCHA v3 |
| `MEDIDESK_CAPTCHA_MIN_SCORE` | `0.3` | Minimalny akceptowany score |
| `MEDIDESK_CAPTCHA_ENTERPRISE` | `false` | `true` = `ReCaptchaV3EnterpriseTaskProxyLess` |
| `MEDIDESK_CAPTCHA_TIMEOUT` | `60.0` | Budżet czasu na solve (sekundy) |
| `MEDIDESK_RECAPTCHA_BRIDGE_URL` | — | Override URL dla bridge/solver (domyślnie `https://app.medidesk.io/forms/{form_id}`) |

**Stan na 2026-06-01**: Medidesk **tymczasowo wyłączył captchę** — wysyłka zwraca HTTP 200 z tym samym requestem, którego użyjemy gdy captcha wróci. Pełna diagnoza, dowody i wzór wiadomości do Medideska: [`captcha_diagnoza.md`](captcha_diagnoza.md).

### Diagnostyka — endpointy `/debug/*`

Endpointy `/debug/captcha` i `/debug/send` są chronione shared-tokenem (`MEDIDESK_DEBUG_TOKEN`). Bez tokenu w env zwracają **503**. Z tokenem w env:

```bash
# Preferowane — header
curl -H "X-Debug-Token: $TOKEN" "https://md-integrator-old.onrender.com/debug/captcha"

# Wygoda w przeglądarce — query param
https://md-integrator-old.onrender.com/debug/captcha?token=$TOKEN
```

Zły / brak tokenu → **401**. Porównanie tokenu w `hmac.compare_digest` (constant-time).

### Metadane aplikacji

Centralne ustawienia UI (wstrzykiwane do szablonów przez Jinja2):

| Zmienna | Domyślna | Gdzie widoczna |
|---|---|---|
| `MEDIDESK_APP_NAME` | `Integracja Leadów do Medidesk` | `<title>`, sidebar, landing |
| `MEDIDESK_APP_VERSION` | `2.0.0` | `<meta name="version">` |
| `MEDIDESK_APP_AUTHOR` | `Aga - Marketing` | `<meta name="author">` |
| `MEDIDESK_APP_ICON_PATH` | `/static/icon.jpg` | favicon, sidebar, landing |

## Uruchamianie lokalne

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Testy

```bash
pytest
```

## Dokumenty powiązane

- [DEPLOYMENT.md](DEPLOYMENT.md) — Wdrożenie na Render, znane problemy
- [CHANGELOG.md](CHANGELOG.md) — Historia zmian i wersji
