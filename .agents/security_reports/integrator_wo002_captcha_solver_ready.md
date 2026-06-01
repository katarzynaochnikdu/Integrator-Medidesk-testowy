# 🛡 SecGate Report — WO#002 Captcha Solver Ready

**Data**: 2026-06-01
**WO**: `.agents/work_orders/integrator_wo002_captcha_solver_ready.md`
**Snapshot**: `przed_captcha_solver_ready_20260601`
**Werdykt**: ✅ **PASS** (z 1 zastrzeżeniem do osobnego WO)

## Zakres audytu

WO#002 to cleanup + dokumentacja — kod (`app/captcha_provider.py`, `app/medidesk_client.py`, `app/captcha_bridge.py`, `app/config.py`) **nie był modyfikowany**. Audyt obejmuje:

1. Diff (`docs/README.md`, `docs/CHANGELOG.md`, `integrator_system_state.md`, nowy WO, usunięcie duplikatu).
2. Wprowadzony do dokumentacji site-key — czy to klucz publiczny czy prywatny.
3. Stan kodu solvera, do którego dokumentacja się odwołuje (smoke audit, nie pełny refaktor).

## Wyniki

### ✅ Sekrety i klucze

- **CapSolver API key** (`MEDIDESK_SOLVER_CAPTCHA_API_KEY`) — czytany wyłącznie z env (`app/config.py:17`), używany tylko w `app/captcha_provider.py:101,129` jako `clientKey` do CapSolvera, **nie jest zwracany w żadnej odpowiedzi HTTP**. Endpoint `/debug/captcha` ujawnia tylko `api_key_set: bool` (`app/main.py:50`) — bezpiecznie.
- **Site-key reCAPTCHA** (`6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`) — wpisany do `docs/README.md`. To **klucz publiczny** reCAPTCHA, z definicji widoczny w HTML każdej strony chronionej captchą; pisanie go w docs nie tworzy ryzyka.
- **Brak hardcoded secretów** w nowym tekście (`docs/README.md`, `docs/CHANGELOG.md`, `integrator_wo002_*.md`).

### ✅ Diff tylko dokumentacja

Brak zmian w kodzie aplikacji — brak nowych powierzchni ataku, brak nowych endpointów, brak zmian w auth/SQL/template renderingu.

### ✅ Auth na ścieżce produkcyjnej

`POST /webhook/facebook` → `submit_form_urlencoded` → `get_captcha_token` → CapSolver. Webhook chroniony FB-owym signature check, integracja po `(fb_page_id, fb_form_id)`. Ścieżka bez zmian.

### ⚠️ ZASTRZEŻENIE — `/debug/*` bez admin-gate

**Findings** (poza zakresem WO#002, ale wykryte w trakcie audytu):

- `app/main.py:41` `@app.get("/debug/captcha")` — brak `Depends(require_admin)`.
- `app/main.py:71` `@app.get("/debug/send")` — brak `Depends(require_admin)`.

Konwencja projektu (`CLAUDE.md`, sekcja „Conventions"):
> Diagnostic endpoints under `/debug/*` exist and are admin-gated (`Depends(require_admin)`).

**Ryzyko**:
- `/debug/captcha` ujawnia `mode`, `site_key_set`, `api_key_set`, `website_url`, długość tokenu i jego pierwsze 40 znaków (token jest jednorazowy + ~2min TTL → niskie ryzyko).
- `/debug/send` wysyła rzeczywisty POST do Medideska z syntetycznymi danymi przy każdym wywołaniu — możliwy spam endpoint Medideska + spalenie kredytów CapSolvera przez nieautoryzowanego odwiedzającego.

**Rekomendacja**: utworzyć osobny WO (#003) → dodać `Depends(require_admin)` do obu endpointów. Nie w zakresie #002 (WO mówi: „nie modyfikujemy kodu solvera/medidesk_client/diagnostyki — baseline 200").

### ✅ ENV checklist w docs/README.md

Wymagane zmienne dla solvera są poprawnie wymienione (`MEDIDESK_SOLVER_CAPTCHA_API_KEY`, `MEDIDESK_RECAPTCHA_SITE_KEY`). Bez `_SECRET` w nazwach — Render nie zaszyfruje per nazwa, ale obie są w sekcji „zmienne środowiskowe" Rendera (poza repo).

## Werdykt

✅ **PASS** dla WO#002 (zmiany dokumentacyjne nie wprowadzają regresji bezpieczeństwa).

⚠️ Osobne WO/bug do założenia: **Admin-gating `/debug/captcha` i `/debug/send`**.

---

**Auditor**: 🛡 Security Worker (Master Agent flow)
