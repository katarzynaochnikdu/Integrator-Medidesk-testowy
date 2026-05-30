# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Medidesk Integrator** — FastAPI app that bridges Facebook Lead Ads → Medidesk via webhooks. Production at https://md-integrator-old.onrender.com (Render Starter tier, Frankfurt, auto-deploy from `main`). User-facing docs and commit messages are in Polish.

## Commands

```bash
# Dev server (Windows / PowerShell — same on Bash)
uvicorn app.main:app --reload --port 8000

# Tests (all)
pytest

# Single test file / case
pytest tests/test_api.py
pytest tests/test_api.py::TestRoot::test_root_redirects_to_login

# Generate a Fernet encryption key (for MEDIDESK_ENCRYPTION_KEY)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

No linter/formatter is configured; do not run repo-wide auto-format. There is no CI — `pytest` is local-only.

## Architecture

Single FastAPI app (`app/main.py` is the router hub and is large — ~1500 lines). Two routers are mounted: `app.fb_auth.router` (Facebook OAuth + session deps) and `app.webhook.router` (FB lead webhook). Everything else lives directly on `app` in `main.py`.

**Request flow for leads:** Facebook → `POST /webhook/facebook` (`app/webhook.py`) → looks up integration by `(fb_page_id, fb_form_id)` via `integrations_store.find_by_fb_page_and_form` → maps FB fields to Medidesk fields using stored `field_mappings` (+ type-aware consent handling) → `medidesk_client.submit_form_urlencoded` POSTs to `https://app.medidesk.io/api/forms/{id}` → `lead_tracker.log_lead_event` writes a row to `lead_events`.

**Storage layer:** SQLite (`medidesk.db`) via `app/db.py` (WAL mode, single shared connection, `check_same_thread=False`). Tables: `integrations`, `lead_events`, `sessions`, `session_audit`, `facilities`, `users`, `user_facilities`, `facility_invites`, `pending_registrations`, `integrations_audit`. Schema is created lazily by `get_connection()`; new columns are added via `_safe_add_column` (ALTER TABLE that swallows "already exists"). FB page tokens and session access tokens are encrypted at rest with Fernet when `MEDIDESK_ENCRYPTION_KEY` is set (dev falls back to plaintext).

**Auth and access control (`app/fb_auth.py`):**
- Session stored server-side in SQLite `sessions` table; client gets a signed cookie (`fb_session`) carrying only the session ID (HMAC-SHA256, 16-char tag). 3h TTL, sliding on last activity (DB write throttled to once per 60s).
- Roles: `owner`, `admin`, `user`, `viewer` (defined in `app/users_store.py` `ROLES`). Legacy sessions may have `"user"` and are treated as owner-equivalent until re-login.
- Dependencies used across endpoints: `require_auth`, `require_admin`, `require_facility`, `require_write_role`. `require_facility` lets admin bypass; others need a `facility_id`. `require_write_role` rejects `viewer`.
- A user can belong to multiple facilities (`user_facilities` table). `main._session_facility_ids` joins primary facility with all active memberships — required to avoid 403s for multi-facility users. `_check_integration_access` is the per-integration gate.

**Templates (`app/templates/`):** Jinja2 with a single `base.html` layout. All HTML endpoints go through `main.render_template(request, name, **kwargs)`, which injects `app_name`, `app_version`, `app_author`, `app_admin_email`, `app_icon_path` from `settings`. The two largest views are `dashboard.html` (~3.5k lines) and `setup_wizard.html` (~2.5k lines); prefer surgical edits over rewrites. Static assets are mounted at `/static` from `app/static/` — `theme.css` defines CSS variables for light/dark mode, `theme.js` reads `localStorage`/`prefers-color-scheme` synchronously in `<head>` to prevent FOIT.

**Startup tasks (`main.startup_db`):** initializes SQLite, runs `migrate_from_json()` (idempotent JSON→SQLite migration for legacy installs), loads the admin password from `<data_dir>/.admin_password` (auto-bcrypts plaintext on first read), and spawns two asyncio loops: token-health check every 24h (`app/alerting.py`) and orphan lead purge every 1h (deletes soft-deleted lead events past the 72h grace window).

## Configuration

All env vars use the `MEDIDESK_` prefix (`pydantic-settings` with `env_prefix="MEDIDESK_"` in `app/config.py`). Required in production: `MEDIDESK_FB_APP_ID`, `MEDIDESK_FB_APP_SECRET`, `MEDIDESK_FB_REDIRECT_URI`, `MEDIDESK_ENCRYPTION_KEY`, `MEDIDESK_FB_SESSION_SECRET`, `MEDIDESK_ADMIN_PASSWORD`, `MEDIDESK_ADMIN_EMAIL`, `MEDIDESK_DATA_DIR` (set to `/data` on Render paid plan; defaults to `.` locally). See `docs/README.md` for the full list.

## Known gotchas (must respect when changing code)

1. **Python 3.14 on Render** — Render ignores `PYTHON_VERSION: "3.12.0"` from `render.yaml` and installs 3.14, which crashes Jinja2's default `LRUCache` with `unhashable type: 'dict'`. The fix is `Environment(..., cache_size=0)` in `main.py`. Do not re-enable caching.
2. **Starlette ≥0.28 `TemplateResponse` signature** — `render_template()` wraps the call in `try/except TypeError` to support both old (`name, context`) and new (`request, name, context`) signatures. Keep that pattern when adding template renders, or just use `render_template()`.
3. **Render Free tier has no persistent disk** — `medidesk.db` is wiped on every deploy. On the paid plan, set `MEDIDESK_DATA_DIR=/data` and mount a disk.
4. **Cold starts** — Free tier sleeps after ~15 min; first request takes 30–60s.
5. **`fb_session` cookie is `secure=True`** — only sent over HTTPS. Local dev over plain HTTP works because the cookie is set; just don't switch to non-HTTPS in production.

## Conventions

- **Commit format:** `type: description` (e.g. `fix: …`, `feat: …`, `refactor: …`, `docs: …`, `ui: …`, `cleanup: …`). Messages are typically Polish.
- **New HTML endpoint:** `@app.get("/path")` → `return render_template(request, "name.html")`. Don't reach for `HTMLResponse(read_text())` — that pattern was replaced in 2.0.0.
- **New template variable available everywhere:** add to `Settings` in `app/config.py`, then add to the `context` dict in `render_template()` in `main.py`.
- **Audit trail:** mutations to integrations should call `main._audit(request, session, action, ...)` which writes to `integrations_audit` via `users_store.log_integration_action`. Use `_integration_snapshot(i)` to produce the before/after blob (it strips tokens).
- **Diagnostic endpoints** under `/debug/*` exist and are admin-gated (`Depends(require_admin)`); if you add a temporary one for debugging, gate it the same way and remove it after.

## Agent / Cursor rules (`.cursor/rules/`, `.agents/`)

This repo uses a multi-agent workflow defined in `.cursor/rules/integrator_*.mdc` and mirrored in `.agents/workers/`. The Master agent orchestrates and delegates to specialized workers. Roster:

| Worker | Rola |
|---|---|
| 🎯 Master Agent | Orkiestrator — klasyfikuje, tworzy WO, deleguje, weryfikuje gates |
| 🔍 Research/Inventory | Czysta analiza, NIE modyfikuje |
| 🧬 Code Analyst | Dekompozycja kodu (przepływ, zależności, ryzyka) |
| ⚙️ Implementer | Pisze kod w ścisłym zakresie WO |
| 🐛 Debugger | Reprodukcja → fix chirurgiczny |
| 🧪 QA/UI Tester | Test w przeglądarce, screenshot, raport |
| 📝 Technical Writer | Pisze dokumentację (gdy WO tego wymaga) |
| 📝 Documentation Keeper | **Gate obowiązkowy** — sprawdza spójność docs/CHANGELOG/context/CLAUDE.md po każdym WO |
| 🛡 Security | **Gate obowiązkowy** — audyt diffa (sekrety, auth, SQL, XSS, tokeny, audit) po każdym WO |
| 📸 Snapshot/State Saver | Git tag przed niebanalną zmianą |

**Definition of Done dla WO z kodem**: Implementacja ✅ + QA Gate (jeśli UI/API) ✅ + 🛡 SecGate PASS ✅ + 📝 DocGate PASS ✅. Bez gates WO nie jest zamknięty.

**Slash commands** (`.claude/commands/`):
- `/master` — aktywuje Master Agenta, klasyfikuje zadanie, proponuje flow
- `/wo <tytuł>` — tworzy szkielet Work Ordera (nie deleguje)
- `/bug <opis>` — szybka ścieżka bug → WO dla Debuggera
- `/idea <opis>` — zapis do backlogu (`.agents/ideas/`), bez WO

Kluczowe zasady dla Claude Code:
- **Snapshot before non-trivial changes:** `git tag przed_<desc>_YYYYMMDD` and push it. Existing safety tag: `przed_refactoringiem`.
- **Strict scope per change:** modify only the files the task names; don't piggyback refactors onto bug fixes; don't auto-format files outside the scope.
- **Preserve existing comments and docstrings** when editing — they encode constraints (the "why").
- **Update `docs/CHANGELOG.md`** for any user-visible change. Format is Keep a Changelog (Polish). DocGate fails the WO without this.
- **For UI changes:** verify endpoints return 200 and the browser console is clean before declaring done. The QA worker's smoke list is: `/login`, `/admin`, `/dashboard`, `/setup`, `/privacy`, `/tos`, `/data-deletion`, `/static/icon.jpg`, `/static/theme.css`, `/static/theme.js`.
- `.agents/context/integrator_project_context.md` and `integrator_system_state.md` track current state and are read by agents at task start; update `integrator_system_state.md` when status, known problems, or safety tags change.
- SecGate / DocGate raports land in `.agents/security_reports/` and `.agents/doc_reports/` respectively, named `integrator_woNNN_<slug>.md`.
