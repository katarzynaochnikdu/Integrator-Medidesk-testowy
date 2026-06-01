# Wdrożenie — Medidesk Integrator

## Platforma: Render.com

- **Plan**: Starter (płatny)
- **Region**: Frankfurt
- **Auto-deploy**: Tak (z `main` branch)
- **URL**: https://md-integrator-old.onrender.com
- **Repo**: https://github.com/katarzynaochnikdu/Integrator-Medidesk-testowy (po renamie z `MD_integrator_V1` — GitHub trzyma redirect, Render auto-deploy działa dalej)

### Komendy

```yaml
buildCommand: pip install -r requirements.txt
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
healthCheckPath: /
```

### Persistent Disk

Na planie Free brak persistent disk. Baza SQLite (`medidesk.db`) jest odtwarzana przy każdym deployu. Na planie płatnym ustaw `MEDIDESK_DATA_DIR=/data` i zamontuj dysk pod `/data`.

---

## Znane problemy i obejścia

### ⚠ Python 3.14 na Render (kwiecień 2026)

**Problem**: Render ignoruje `PYTHON_VERSION: "3.12.0"` z `render.yaml` i instaluje Python 3.14. To powoduje crash Jinja2 `LRUCache` (`unhashable type: 'dict'`).

**Obejście zastosowane w kodzie**:
```python
# app/main.py
_jinja_env = Environment(
    loader=FileSystemLoader(...),
    cache_size=0,  # Wyłącza LRUCache — Python 3.14 compat
)
```

**Zalecenie**: Wymuś wersję Pythona w panelu Render (Settings → Environment → Python Version) zamiast polegać na `render.yaml`.

### ⚠ Starlette TemplateResponse — zmiana sygnatury

**Problem**: Starlette >=0.28 zmienił sygnaturę `TemplateResponse`. Stara: `TemplateResponse(name, context)`. Nowa: `TemplateResponse(request, name, context)` lub keyword args.

**Obejście zastosowane w kodzie**:
```python
try:
    return templates.TemplateResponse(request=request, name=name, context=context)
except TypeError:
    return templates.TemplateResponse(name, context)
```

### Free tier — cold starts

Render Free tier usypia serwer po ~15 min nieaktywności. Pierwszy request po uśpieniu trwa 30-60 sekund. Rozwiązanie: przejście na płatny plan ($7/mies) lub dodanie zewnętrznego pinga (np. UptimeRobot).

---

## Zmienne środowiskowe na Render

Ustaw w: Dashboard → md-integrator-old → Environment → Environment Variables.

> ⚠ **Uwaga przy zmianie URL produkcji**: jeśli URL serwisu się zmienia, równolegle zaktualizuj `MEDIDESK_FB_REDIRECT_URI` (zmienna na Render) **i** redirect URI w Facebook Developer Console — inaczej OAuth padnie.

Obowiązkowe:
- `MEDIDESK_FB_APP_ID`
- `MEDIDESK_FB_APP_SECRET`
- `MEDIDESK_FB_REDIRECT_URI` = `https://md-integrator-old.onrender.com/auth/facebook/callback`
- `MEDIDESK_ENCRYPTION_KEY` (wygeneruj: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `MEDIDESK_FB_SESSION_SECRET`
- `MEDIDESK_ADMIN_PASSWORD`
- `MEDIDESK_ADMIN_EMAIL`

Captcha (Medidesk reCAPTCHA v3, zob. `docs/README.md` → sekcja „Captcha — tryby i ENV"):
- `MEDIDESK_CAPTCHA_MODE` = `solver` (oficjalnie produkcyjnie)
- `MEDIDESK_SOLVER_CAPTCHA_API_KEY` = clientKey CapSolver
- `MEDIDESK_RECAPTCHA_SITE_KEY` = `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`
- `MEDIDESK_CAPTCHA_HEADER` = `enterprise-recaptcha-response` (default OK)
- `MEDIDESK_CAPTCHA_ENTERPRISE` = `true` / `false` (zob. README)

Diagnostyka:
- `MEDIDESK_DEBUG_TOKEN` — shared token chroniący `/debug/*`. **Bez tego endpointy odpowiadają 503 (fail-closed).** Wygeneruj: `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Użycie: `curl -H "X-Debug-Token: $TOKEN" .../debug/captcha`.

---

## Tagi i wersjonowanie

| Tag | Opis |
|---|---|
| `przed_refactoringiem` | Ostatni commit przed refaktoryzacją na Jinja2 |
| `przed_captcha_bridge_20260530` | Przed pracami nad reCAPTCHA bridge |
| `przed_captcha_solver_ready_20260601` | Przed cleanup-em WO#002 (solver oficjalny) |
| `przed_debug_admingate_20260601` | Przed admin-gating `/debug/*` (WO#003) |
