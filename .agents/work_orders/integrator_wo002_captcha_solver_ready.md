# Work Order #002 — Captcha Solver Ready (CapSolver)

**Data**: 2026-06-01
**Worker**: ⚙️ Implementer + 🛡 SecGate + 📝 DocGate
**Priorytet**: 🟡 Normalny
**Snapshot**: `przed_captcha_solver_ready_20260601`

### Cel

Sformalizować i utrzymać gotową, działającą bibliotekę solver (CapSolver) jako oficjalną ścieżkę dostarczania tokenu reCAPTCHA v3 do Medideska — tak aby w momencie, gdy Medidesk **ponownie włączy captchę**, wysyłka leadów dalej działała bez zmian w kodzie ani w configu.

### Kontekst

- **2026-06-01**: Medidesk **tymczasowo wyłączył captchę**. `POST /api/forms/kochnikmini` → **HTTP 200**, lead przyjmowany. To nasz baseline DZIAŁAJĄCY (zob. `docs/captcha_diagnoza.md` sekcja 0).
- Kod solvera jest **w pełni napisany i wdrożony** (`app/captcha_provider.py`, `app/medidesk_client.py`, `app/config.py`). Commity: `5127542`, `9aba701`, `442c299`.
- Świadoma decyzja: **nie zmieniamy niczego w konfiguracji** wysyłki — gdy captcha wróci, jedyną nową zmienną będzie weryfikacja tokenu po stronie Medideska.
- Bridge (Playwright) zostaje jako **alternatywa/fallback** — nie usuwamy.

### Zakres

**W zakresie (DO)**:
- [x] Snapshot: `git tag przed_captcha_solver_ready_20260601`
- [x] Usunąć duplikat `captcha_diagnoza.md` z roota repo (plik istnieje w `docs/`, root jest identyczny)
- [x] Dopisać sekcję „Captcha — tryby i ENV" do `docs/README.md` (solver/bridge/none + lista wymaganych zmiennych + link do diagnozy)
- [x] Wpis w `docs/CHANGELOG.md` — baseline HTTP 200 + solver jako oficjalna ścieżka, bridge jako fallback
- [x] Aktualizacja `.agents/context/integrator_system_state.md` — WO#002 → Wykonane, status wysyłki, nowy tag
- [x] 🛡 **SecGate**: PASS — raport w `.agents/security_reports/integrator_wo002_captcha_solver_ready.md`
- [x] 📝 **DocGate**: PASS — raport w `.agents/doc_reports/integrator_wo002_captcha_solver_ready.md`

**Poza zakresem (NIE RÓB)**:
- Modyfikacja `app/captcha_provider.py`, `app/medidesk_client.py`, `app/captcha_bridge.py` — działa, baseline 200 osiągnięty
- Zmiana endpointów, formatu body (`fieldsValues[fieldId]=value`), nagłówka (`enterprise-recaptcha-response`), site-key'a
- Usuwanie `captcha_bridge.py` / Playwright z `requirements.txt` — bridge zostaje jako fallback
- Wyłączanie `/debug/send` (admin-gated, potrzebne do diagnostyki, gdy captcha wróci)
- Zmiana ENV-ów na Renderze (uznane za już ustawione przez użytkownika)

### Pliki do modyfikacji

| Plik | Oczekiwana zmiana |
|---|---|
| `captcha_diagnoza.md` (root) | **DELETE** (duplikat) |
| `docs/README.md` | Dodać sekcję „Captcha — tryby i ENV" |
| `docs/CHANGELOG.md` | Wpis baseline + solver oficjalny |
| `.agents/context/integrator_system_state.md` | WO#002 → Wykonane, nowy tag |

### Kryteria akceptacji

- [ ] `git status -s` → nie pokazuje `captcha_diagnoza.md` w root jako untracked
- [ ] `docs/README.md` zawiera sekcję opisującą `MEDIDESK_CAPTCHA_MODE` (solver/bridge/none) i wymagane ENV-y dla solvera
- [ ] `docs/CHANGELOG.md` zawiera wpis 2026-06-01 z opisem baseline + solver
- [ ] `integrator_system_state.md` — WO#002 w „Wykonane", tag `przed_captcha_solver_ready_20260601` na liście
- [ ] 🛡 **SecGate**: PASS — raport potwierdza brak hardcoded secretów, admin-gating `/debug/*`
- [ ] 📝 **DocGate**: PASS — raport potwierdza spójność CHANGELOG ↔ README ↔ state ↔ kod

### Ograniczenia

- Nie modyfikować logiki captcha (kod jest baseline DZIAŁAJĄCY → znany-dobry stan, zostaje 1:1)
- Zachować kompatybilność z Python 3.14 (nie wymaga zmian)
- Commit message: `docs: WO#002 solver gotowy na powrót captchy + cleanup` (typ `docs:` bo zmiany tylko w dokumentacji)

### Notatki

- Baseline 200 = wszystko poza weryfikacją tokenu jest poprawne (endpoint, body, mapowanie, nagłówek, klucz). Dowód w `docs/captcha_diagnoza.md` sekcja 0.
- Otwarte pytanie do Medideska (na powrót captchy): co zwraca ich `createAssessment` dla naszych tokenów (`tokenProperties.valid`, `score`, `expectedAction`). Wzór wiadomości w `docs/captcha_diagnoza.md` sekcja 4.
- Domyślny config `app/config.py:15-22`:
  - `captcha_mode = "solver"`
  - `captcha_header = "enterprise-recaptcha-response"`
  - `captcha_action = "submit"`, `captcha_min_score = 0.3`, `captcha_enterprise = False`
- ENV produkcyjne wymagane: `MEDIDESK_SOLVER_CAPTCHA_API_KEY`, `MEDIDESK_RECAPTCHA_SITE_KEY` (= `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`).

---

**Status**: ✅ Wykonane (2026-06-01)
