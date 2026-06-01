# Kontekst Projektu — Medidesk Integrator

> Ten plik jest ładowany przez KAŻDEGO workera jako punkt wejścia.

## Identyfikacja

- **Nazwa**: Medidesk Integrator (Integracja Leadów do Medidesk)
- **Wersja**: 2.0.0
- **Repo**: https://github.com/katarzynaochnikdu/Integrator-Medidesk-testowy
- **Produkcja**: https://md-integrator-old.onrender.com
- **Framework**: FastAPI (Python)
- **Szablony**: Jinja2 z `base.html` layoutem
- **Baza**: SQLite (`medidesk.db`)
- **Hosting**: Render.com (Free tier, Frankfurt)

## Kluczowe pliki

| Plik | Rola |
|---|---|
| `app/main.py` | Główny router (~1470 linii) — endpointy, middleware, startup |
| `app/config.py` | Konfiguracja (pydantic-settings), metadane aplikacji |
| `app/templates/base.html` | Layout bazowy — head, meta, theme scripts |
| `app/templates/dashboard.html` | Największy widok (~3570 linii) — panel zarządzania |
| `app/templates/setup_wizard.html` | Kreator integracji (~2450 linii) |
| `app/static/theme.css` | Zmienne CSS (Light/Dark mode foundation) |
| `app/static/theme.js` | Sync theme detection (FOIT prevention) |
| `app/db.py` | Schema SQLite + migracje |
| `app/webhook.py` | Handler webhooków Facebook |

## Konwencje

- **Commit messages**: `type: description` (fix/feat/refactor/docs/cleanup)
- **Zmienne środowiskowe**: prefix `MEDIDESK_` (np. `MEDIDESK_FB_APP_ID`)
- **Endpointy HTML**: renderowane przez `render_template(request, "nazwa.html")`
- **Snapshoty**: `git tag nazwa_tagu` przed większymi zmianami
- **Python na Render**: 3.14 (nie 3.12!). Testuj kompatybilność.

## Ograniczenia

- Render Free tier = brak persistent disk (DB resetuje się przy deploy)
- Max 15 min nieaktywności → cold start
- Jinja2 wymaga `cache_size=0` (Python 3.14 compat)
- `TemplateResponse` wymaga try/except (Starlette compat)
