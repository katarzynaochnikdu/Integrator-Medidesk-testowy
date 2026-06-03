# System State — Medidesk Integrator

> Ostatnia aktualizacja: 2026-06-03 (branch `main`, po WO#007 — przekazywalna specyfikacja wdrożeniowa `docs/INTEGRACJA_MEDIDESK.md`)

## Status projektu

| Element | Status | Uwagi |
|---|---|---|
| Wysyłka do Medideska | ✅ **DZIAŁA (200)** | Medidesk **tymczasowo** wyłączył captchę. Baseline udokumentowany w `docs/captcha_diagnoza.md` sekcja 0. NIE zmieniać configu. Solver (CapSolver) gotowy na powrót captchy — WO#002 zamknięty 2026-06-01. **WO#004 (zamknięty 2026-06-03):** klient POST-uje **wyłącznie na UUID (formTemplateId) + token** — `resolve_submit_form_id`/webFormId usunięte. Live 200 potwierdzone w produkcji przez `/demo/contact` (form `e8342a6a`, „OK — lead wysłany"). |
| Produkcja (Render) | ✅ Działa | https://md-integrator-old.onrender.com |
| Lokalny dev | ✅ Działa | `uvicorn app.main:app --reload` |
| Testy | ⚠️ Brak CI | `pytest` lokalnie |
| Git | 🔄 Branch | `feat/medidesk-captcha-bridge`, tag `przed_captcha_bridge_20260530` |

## Ostatni deploy

- **Commit**: `c1b1ddf` — `rename: prefix all agent files with integrator_`
- **Wersja**: 2.0.0
- **Python na Renderze**: 3.14 (UWAGA: ignoruje render.yaml!)

## Aktywne Work Ordery

| WO | Tytuł | Status | Plik |
|---|---|---|---|
| #001 | Dark Mode (Jasny/Ciemny/Systemowy) | 🔄 W trakcie | `.agents/work_orders/integrator_wo001_dark_mode.md` |

## Wykonane Work Ordery

| WO | Tytuł | Zamknięcie | Plik |
|---|---|---|---|
| #002 | Captcha solver ready (CapSolver oficjalny, bridge fallback) | 2026-06-01 | `.agents/work_orders/integrator_wo002_captcha_solver_ready.md` |
| #003 | Admin-gating `/debug/*` (token-based, fail-closed) | 2026-06-01 | `.agents/work_orders/integrator_wo003_debug_admin_gate.md` |
| #004 | Wysyłka tylko na UUID (usunięcie webFormId/dual-endpoint) | 2026-06-03 | `.agents/work_orders/integrator_wo004_uuid_only_submit.md` |
| #005 | Test captchy na `/demo/contact` (zły→dobry token) + fix presetów | 2026-06-03 | `.agents/work_orders/integrator_wo005_demo_captcha_test.md` |
| #006 | Docs: aktualny kontrakt captchy (nadrzędny nad starym PDF) + fix endpointu w README | 2026-06-03 | `.agents/work_orders/integrator_wo006_doc_captcha_contract.md` |
| #007 | Przekazywalna specyfikacja wdrożeniowa `docs/INTEGRACJA_MEDIDESK.md` | 2026-06-03 | `.agents/work_orders/integrator_wo007_integration_spec.md` |

## Aktywne prace

- [x] Refaktoring na Jinja2 + base.html
- [x] Centralizacja metadanych (config.py)
- [x] Fundament theme (CSS vars + JS)
- [x] System agentów (.agents/)
- [x] Dokumentacja projektu (docs/)
- [ ] **WO#001**: Wdrożenie Dark Mode (zamiana hardcoded kolorów na CSS vars)
- [ ] **WO#001**: Przełącznik theme w UI (toggle w dashboardzie)
- [ ] **WO#001**: Weryfikacja czytelności komponentów w trybie ciemnym

## Znane problemy

| Problem | Status | Obejście |
|---|---|---|
| Python 3.14 na Render — Jinja2 LRUCache crash | ✅ Obejście | `cache_size=0` w Environment |
| Starlette TemplateResponse zmiana sygnatury | ✅ Obejście | try/except w `render_template()` |
| Render Free tier — cold starts 30-60s | ℹ️ Nieaktualne | Serwis na planie Starter (płatny) |
| Medidesk reCAPTCHA v3 wymagana na endpointcie POST | ✅ Gotowe (czeka na powrót captchy) | Solver (CapSolver) jako oficjalna ścieżka — `MEDIDESK_CAPTCHA_MODE=solver`, nagłówek `enterprise-recaptcha-response`. Bridge (Playwright) jako fallback. Baseline 200 osiągnięty z captchą OFF; ten sam request zadziała po jej powrocie. Pełna diagnoza: `docs/captcha_diagnoza.md`. |
| Medidesk zwraca 500 zamiast 401 przy braku/błędnym tokenie | ❗ Bug po stronie Medideska | Do zgłoszenia. Spec mówi 401 (PDF str. 3), faktycznie leci 500. **Potwierdzone WO#004:** 500 to objaw braku/złego tokenu, nie złego endpointu — klient POST-uje na UUID. |
| Repo „testowy" rozjechane z pełną wersją: `app/config.py` nie ma `data_dir`/`demo_page_enabled`, brak route'ów `/`, `/api/info` → pytest pokazuje 7 failed + 12 errors (pre-existing, NIE z WO#004). Lokalny Python (PyManager 3.14) nie weryfikuje cert SSL Medideska. | ℹ️ Znane, pre-existing | Live-testy MD wykonywać na Render (env + CA OK). Pełny zielony pytest wymaga sync `config.py`↔`db.py` — kandydat na osobny WO. |
| `_invite_html()` — inline HTML (nie Jinja2) | ℹ️ Celowe | Izolowany endpoint |

## Tagi bezpieczeństwa

| Tag | Commit | Opis |
|---|---|---|
| `przed_refactoringiem` | `f96b4eb` | Przed migracją na Jinja2 |
| `przed_captcha_bridge_20260530` | `7451f7a` | Przed pracami nad reCAPTCHA bridge + URL cleanup (snapshot main) |
| `przed_captcha_solver_ready_20260601` | `5127542` | Przed cleanup-em WO#002 (usunięcie duplikatu diagnozy, sekcja README, CHANGELOG) |
| `przed_debug_admingate_20260601` | `51ebaf4` | Przed admin-gating `/debug/*` (WO#003) |
| `przed_uuid_only_submit_20260603` | `cb17031` | Przed przejściem wysyłki na UUID-only (WO#004) |
| `przed_demo_captcha_test_20260603` | `d3c79a5` | Przed testem captchy + fix presetów na /demo/contact (WO#005) |
