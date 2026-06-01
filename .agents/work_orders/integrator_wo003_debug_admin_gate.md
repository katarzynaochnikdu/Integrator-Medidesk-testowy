# Work Order #003 — Admin-gating `/debug/*` (token-based)

**Data**: 2026-06-01
**Worker**: ⚙️ Implementer + 🛡 SecGate + 📝 DocGate
**Priorytet**: 🟡 Normalny (zgłoszone przez SecGate #002)
**Snapshot**: `przed_debug_admingate_20260601`

### Cel

Zabezpieczyć diagnostyczne endpointy `/debug/captcha` i `/debug/send` przed nieautoryzowanym dostępem. Bez gate'a anonimowy ruch może spamować POST-y do Medideska i palić kredyty CapSolvera.

### Kontekst

- SecGate WO#002 (`.agents/security_reports/integrator_wo002_captcha_solver_ready.md`) wskazał, że `/debug/captcha` (`app/main.py:41`) i `/debug/send` (`app/main.py:71`) nie mają żadnego gate'a, łamiąc konwencję `CLAUDE.md` („Diagnostic endpoints under `/debug/*` exist and are admin-gated").
- **Stan gałęzi `main`**: stripped-down captcha-diagnostic — `main.py` 189 linii, brak routerów logowania, sesji, dashboardu. `require_admin` w `fb_auth.py` istnieje, ale nie ma jak utworzyć sesji (brak `/login`). → `Depends(require_admin)` zablokowałoby endpoint również dla nas.
- Pragmatyczne rozwiązanie: **shared token w env** (`MEDIDESK_DEBUG_TOKEN`) sprawdzany przez nagłówek `X-Debug-Token` (preferowane) lub query param `?token=...` (wygoda w przeglądarce).
- Gdy gałąź zostanie zmergowana z pełnym systemem (sesje + `require_admin`) → migracja na `Depends(require_admin)` w osobnym WO.

### Zakres

**W zakresie (DO)**:
- [x] Snapshot: `git tag przed_debug_admingate_20260601`
- [x] Dodać `debug_token: str = ""` do `Settings` w `app/config.py`
- [x] Dodać dependency `require_debug_token(request)` w `app/main.py` (sprawdza `X-Debug-Token` header lub `?token=` query; 401 gdy brak/zły token; 503 gdy `debug_token` nieskonfigurowany — fail-closed)
- [x] Owrap `/debug/captcha` i `/debug/send` w `Depends(require_debug_token)`
- [x] Dokumentacja w `docs/README.md` — nowa zmienna env w tabeli + sekcja jak używać `/debug/*`
- [x] Wpis w `docs/CHANGELOG.md` — fix bezpieczeństwa
- [x] Aktualizacja `integrator_system_state.md` — WO#003 → Wykonane, tag, „Znane problemy" zaktualizowane
- [x] 🛡 SecGate: PASS — raport
- [x] 📝 DocGate: PASS — raport
- [x] Bonus: rename repo `MD_integrator_V1` → `Integrator-Medidesk-testowy` + update URL-i w docs

**Poza zakresem (NIE RÓB)**:
- Nie wprowadzaj `Depends(require_admin)` — brak sesji na tej gałęzi
- Nie ruszaj `/api/forms/*` ani `/api/submit/*` (legalne API, nie diagnostyka)
- Nie zmieniaj logiki captcha ani Medidesk clienta
- Nie hardcoduj tokenu — tylko env

### Pliki do modyfikacji

| Plik | Zmiana |
|---|---|
| `app/config.py` | `+ debug_token: str = ""` |
| `app/main.py` | `+ require_debug_token` dependency; `Depends(require_debug_token)` na `/debug/captcha` i `/debug/send` |
| `docs/README.md` | sekcja o debug-tokenie + wpis w tabeli ENV |
| `docs/CHANGELOG.md` | wpis 2026-06-01 |
| `.agents/context/integrator_system_state.md` | WO#003 Wykonane, tag, problem zaadresowany |

### Kryteria akceptacji

- [ ] `GET /debug/captcha` bez tokenu → **401 Unauthorized**
- [ ] `GET /debug/captcha?token=<wrong>` → **401**
- [ ] `GET /debug/captcha` z `X-Debug-Token: <correct>` → **200** i zwraca diagnostykę
- [ ] `GET /debug/captcha` gdy `MEDIDESK_DEBUG_TOKEN` puste → **503 "Debug endpoints disabled"** (fail-closed)
- [ ] `docs/README.md`, `docs/CHANGELOG.md`, `integrator_system_state.md` zaktualizowane
- [ ] 🛡 SecGate: PASS
- [ ] 📝 DocGate: PASS

### Ograniczenia

- Python 3.14 compat — bez zmian typowych
- Commit format: `fix(security): admin-gate /debug/* via MEDIDESK_DEBUG_TOKEN`
- ENV `MEDIDESK_DEBUG_TOKEN` musi być ustawione na Renderze **PRZED** wywołaniem endpointu po deploy-u — inaczej fail-closed (503).

### Notatki

- Porównywanie tokenu: `hmac.compare_digest` (constant-time, zapobiega timing attack).
- 401 z `WWW-Authenticate: Bearer` byłby ładny, ale wybieramy prosty 401 + JSON.
- Po deploy-u: użytkownik ustawia `MEDIDESK_DEBUG_TOKEN` w panelu Render (Environment Variables), Render robi auto-redeploy.

---

**Status**: ✅ Wykonane (2026-06-01)
