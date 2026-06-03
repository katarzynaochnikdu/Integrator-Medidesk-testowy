# Changelog — Medidesk Integrator

Wszystkie znaczące zmiany w projekcie są dokumentowane w tym pliku.
Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).

---

## [Unreleased] — 2026-06-03 — WO#006 Dokumentacja: aktualny kontrakt captchy

### Dokumentacja
- **Ujednoznaczniono aktualny kontrakt captchy** jako nadrzędny nad PDF spec (`pliki od medidesk/…Specyfikacja API.pdf`), którego sekcja reCAPTCHA jest **stara**. Aktualne (info Medideska 2026-06-03): nagłówek `enterprise-recaptcha-response`, site-key `6Ldo-f0s…`; stare z PDF: `captcha-response`, `6Lfs81gh…`. Baner „AKTUALNY KONTRAKT" w `docs/captcha_diagnoza.md` + notatka `pliki od medidesk/_UWAGA-aktualnosc-captcha.md`.
- **Poprawiono stary endpoint** w `docs/README.md`: POST idzie na `{formTemplateId}` (UUID), nie `{webFormId}` (zgodnie z WO#004).
- Sekcje 0–4 w `captcha_diagnoza.md` oznaczone jako **historia** (diagnoza maj/czerwiec, captcha ON → 401).

### Uwaga
- Bez zmian w kodzie/configu — wartości captchy są **zmiennymi środowiskowymi** (`MEDIDESK_CAPTCHA_HEADER`, `MEDIDESK_RECAPTCHA_SITE_KEY`, `MEDIDESK_CAPTCHA_ENTERPRISE`), zarządza je użytkownik na Render.

---

## [Unreleased] — 2026-06-03 — WO#005 Test captchy na `/demo/contact`

### Dodane
- **Przycisk „Test captcha: zły token → dobry token"** na `/demo/contact` — wysyła ten sam lead 2×: raz z **zaślepką** (zły token), raz z **prawdziwym** tokenem enterprise, i pokazuje werdykt: captcha **OFF** (zły też przeszedł) / **ON i token przechodzi** (zły odrzucony, dobry OK) / **ON, token odrzucony**. Odpowiada na „czy przechodzę captchę" — samo 200 z demo tego nie mówi, bo demo zawsze dosyła token.

### Naprawione
- **Niespójne dane presetów** na `/demo/contact` — klik „Marek Zieliński" wstawiał dane Anny (przyciski `[Anna, Marek, Ewa]` vs pula danych `[Jan, Anna, Marek]` — przesunięcie indeksów). Wprowadzono pojedyncze źródło prawdy `PEOPLE`; preset N wstawia spójny komplet danych osoby N (imię + e-mail + telefon + …).

### Bezpieczeństwo
- Tag `przed_demo_captcha_test_20260603` jako punkt powrotu.

---

## [Unreleased] — 2026-06-03 — WO#004 Wysyłka tylko na UUID

### Zmienione
- **`submit_form_urlencoded()` POST-uje wyłącznie na UUID (formTemplateId)** — jedyny endpoint zgodny z dokumentacją Medideska. Usunięto logikę „próbuj OBA endpointy" (webFormId + UUID) z commita `9aba701`: była oparta na błędnej diagnozie. HTTP **500 oznaczał brak/niepoprawny token reCAPTCHA** (Medidesk oddaje 500 zamiast dokumentowanego 401), a nie zły endpoint.
- Tag `przed_uuid_only_submit_20260603` jako punkt powrotu.

### Usunięte
- Funkcja `resolve_submit_form_id()` (routing przez `webFormId`) — martwa po przejściu na UUID-only. `fetch_form_definition()` pozostaje (odkrywanie pól przez GET nadal działa).
- Klasa testowa `TestResolveSubmitFormId` → zastąpiona `TestSubmitPostsToUuid` (potwierdza dokładnie jeden POST, na UUID).

### Naprawione
- Mylące docstringi/komentarze w `medidesk_client.py` („POST na UUID → 500, użyj webFormId") — skorygowane: 500 = brak/zły token. Zaktualizowano też wiersz o endpoincie w `docs/captcha_diagnoza.md`.

---

## [Unreleased] — 2026-06-01 — WO#003 Admin-gate `/debug/*`

### Bezpieczeństwo
- **`/debug/captcha` i `/debug/send` chronione shared-tokenem** (`MEDIDESK_DEBUG_TOKEN`). Bez tokenu w env endpoint odpowiada **503 (fail-closed)** — żaden ruch anonimowy nie spali kredytów CapSolver ani nie spamuje Medideska. Z tokenem: `X-Debug-Token` header lub `?token=` query; porównanie w `hmac.compare_digest`.
- Tag `przed_debug_admingate_20260601` jako punkt powrotu.

### Dodane
- `MEDIDESK_DEBUG_TOKEN` (env) — `app/config.py:25` + tabela w `docs/README.md`.
- Sekcja „Diagnostyka — endpointy `/debug/*`" w `docs/README.md` z przykładami curl.

### Naprawione
- Finding SecGate z WO#002 — endpointy diagnostyczne były otwarte dla świata.

---

## [Unreleased] — 2026-06-01 — WO#002 Captcha solver ready

### Bezpieczeństwo
- Tag `przed_captcha_solver_ready_20260601` jako punkt powrotu przed cleanup-em.

### Dodane
- **Sekcja „Captcha — tryby i ENV"** w `docs/README.md` — pełna lista zmiennych dla `solver` / `bridge` / `none`, defaults, link do `docs/captcha_diagnoza.md`.

### Zmienione
- **Solver (CapSolver) — oficjalna ścieżka** dostarczania tokenu reCAPTCHA v3 do Medideska (`MEDIDESK_CAPTCHA_MODE=solver`). Bridge (Playwright) zostaje jako fallback. Kod bez zmian — baseline DZIAŁAJĄCY (HTTP 200) potwierdzony z captchą tymczasowo wyłączoną po stronie Medideska; ten sam request zadziała po jej powrocie.
- **Nagłówek captcha**: `enterprise-recaptcha-response` (Medidesk Enterprise) — utrwalone w defaultach `app/config.py` (commit `442c299`).

### Usunięte
- Duplikat `captcha_diagnoza.md` z roota repo (kanoniczna wersja: `docs/captcha_diagnoza.md`).

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

### Dodane (cd.)
- **Captcha bridge** (`app/captcha_bridge.py`) — headless Chromium (Playwright) generuje tokeny reCAPTCHA v3 dla ścieżki server-to-server (FB webhook → Medidesk).
  Otwiera ``https://app.medidesk.io/forms/{form_id}`` (origin Medideska jest na whiteliście ich site-key'a), woła ``grecaptcha.execute()``, zwraca token.
  Lazy init (start na pierwsze użycie), singleton browser, shutdown w lifespan hook.
  Cichy fallback: gdy Playwright/Chromium nie są dostępne → ``None`` (nie wysadza aplikacji).
- **`medidesk_client.submit_form_urlencoded`** — automatycznie woła bridge gdy wywołujący nie podał ``captcha_response`` (np. ścieżka webhook). Browser-driven path (demo, /api/submit) nadal wysyła własny token z body — bez podwójnej weryfikacji.
- **Endpoint `/debug/captcha-test`** (admin) — szybkie sprawdzenie czy bridge w ogóle wystawia token; zwraca długość, czas i URL bridge'a (bez samego tokenu).
- **`render.yaml` buildCommand** → `playwright install --with-deps chromium`.
- **`requirements.txt`** → `playwright>=1.40`.

### Znane problemy
- **Origin whitelisty reCAPTCHA Medideska — do weryfikacji**: zakładamy, że ``app.medidesk.io`` jest na liście dozwolonych domen site-key'a (Medidesk powinien mieć siebie). Jeśli mają tylko domeny klinik — bridge wystawi niski-score token / odrzucany. W tym wypadku rozwiązaniem jest poproszenie Medideska o dodanie origin'u albo skierowanie bridge'a na URL strony kliniki przez ``MEDIDESK_RECAPTCHA_BRIDGE_URL``.
- **Medidesk zwraca 500 zamiast 401** przy braku/błędnym tokenie — ich bug, do zgłoszenia (PDF spec str. 3 mówi 401).

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
