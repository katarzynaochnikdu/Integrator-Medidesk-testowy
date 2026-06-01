# System State — Medidesk Integrator

> Ostatnia aktualizacja: 2026-06-01 (branch `main`)

## Status projektu

| Element | Status | Uwagi |
|---|---|---|
| Wysyłka do Medideska | ✅ **DZIAŁA (200)** | Medidesk **tymczasowo** wyłączył captchę. Baseline udokumentowany w `docs/captcha_diagnoza.md` sekcja 0. NIE zmieniać configu. |
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
| #002 | Captcha bridge dla FB webhook → Medidesk (Playwright) | 🔄 W trakcie | branch `feat/medidesk-captcha-bridge` |

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
| Medidesk reCAPTCHA v3 wymagana na endpointcie POST | 🔄 W trakcie | Browser-side: ✅ działa (demo). Server-to-server (FB webhook): WIP — Playwright bridge na branchu `feat/medidesk-captcha-bridge` |
| Medidesk zwraca 500 zamiast 401 przy braku/błędnym tokenie | ❗ Bug po stronie Medideska | Do zgłoszenia. Spec mówi 401 (PDF str. 3), faktycznie leci 500. |
| `_invite_html()` — inline HTML (nie Jinja2) | ℹ️ Celowe | Izolowany endpoint |

## Tagi bezpieczeństwa

| Tag | Commit | Opis |
|---|---|---|
| `przed_refactoringiem` | `f96b4eb` | Przed migracją na Jinja2 |
| `przed_captcha_bridge_20260530` | `7451f7a` | Przed pracami nad reCAPTCHA bridge + URL cleanup (snapshot main) |
