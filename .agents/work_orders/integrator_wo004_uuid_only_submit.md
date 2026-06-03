# 📋 Work Order #004

**Data**: 2026-06-03
**Worker**: ⚙️ Implementer (po snapshocie) → 🧪 QA → 🛡 Security → 📝 Doc Keeper
**Priorytet**: 🟡 Normalny
**Snapshot**: `przed_uuid_only_submit_20260603`

### Cel

Uprościć `submit_form_urlencoded()` tak, by POST do Medideska szedł **wyłącznie na UUID (formTemplateId) + poprawnie wygenerowany token reCAPTCHA** — zgodnie z dokumentacją Medideska. Usunąć logikę „próbuj OBA endpointy" (webFormId + UUID) z commita `9aba701`.

### Kontekst

Commit `9aba701` („wysylka probuje OBA endpointy") opierał się na **błędnej diagnozie**: założono, że POST na UUID zwraca 500 z powodu złego endpointu, więc dodano routing przez `webFormId` (`resolve_submit_form_id`) i pętlę próbującą oba identyfikatory.

**Korekta od użytkownika (autorytet domenowy, ma dokumentację Medideska):**
- Poprawny strzał to **UUID + poprawnie wygenerowany token**.
- HTTP **500 oznaczał brak tokenu lub token niepoprawny** — nie zły endpoint.
- `string` / `webFormId` **nie są zgodne z dokumentacją** → nie używamy ich i nie inwestygujemy.

To spójne ze znanym problemem z `integrator_system_state.md` (linia 53): *„Medidesk zwraca 500 zamiast 401 przy braku/błędnym tokenie — Bug po stronie Medideska. Spec mówi 401 (PDF str. 3), faktycznie leci 500."* Czyli 500 na UUID był objawem braku/błędu tokenu, a nie dowodem, że endpoint UUID jest zły.

### Zakres

**W zakresie (DO)**:
- [ ] `app/medidesk_client.py` — `submit_form_urlencoded()`: POST **tylko** na `form_id` (UUID). Usunąć pętlę po `candidates` (webFormId + UUID) i wywołanie `resolve_submit_form_id()`.
- [ ] `app/medidesk_client.py` — usunąć martwą funkcję `resolve_submit_form_id()` (po zmianie nie ma już wywołań poza testami).
- [ ] `app/medidesk_client.py` — poprawić mylące docstringi/komentarze twierdzące „POST na UUID → 500, użyj webFormId". Zastąpić poprawnym uzasadnieniem: **500 = brak/niepoprawny token reCAPTCHA (znany bug MD, spec mówi 401)**. Zachować pozostałe komentarze „dlaczego" (UTF-8 fieldId, siteDomain/siteUrl fallback, Origin/Referer).
- [ ] `tests/test_api.py` — usunąć klasę `TestResolveSubmitFormId` (testuje usuwaną funkcję). Opcjonalnie: dodać test potwierdzający, że `submit_form_urlencoded` POST-uje na UUID (nie na webFormId).
- [ ] `docs/CHANGELOG.md` — wpis o uproszczeniu wysyłki (Keep a Changelog, PL).
- [ ] `docs/captcha_diagnoza.md` — skorygować wiersz o resolve webFormId (linia ~49), by nie sugerował, że webFormId to właściwy endpoint POST.

**Poza zakresem (NIE RÓB)**:
- NIE ruszać `fetch_form_definition()` — nadal potrzebne do odkrywania pól (GET) w `/debug/send` i `/api/forms/{id}/fields`.
- NIE usuwać pola `web_form_id` z `FormDefinition` ani z odpowiedzi `/api/forms/{id}/fields` — to nieszkodliwe metadane z GET, nie routing.
- NIE zmieniać configu captchy ani `MEDIDESK_CAPTCHA_*` (baseline DZIAŁAJĄCY, captcha tymczasowo OFF — `integrator_system_state.md`).
- NIE ruszać nagłówków Origin/Referer/UA, fallbacków siteDomain/siteUrl ani kodowania UTF-8 body.
- NIE piggyback'ować innych refaktorów.

### Pliki do modyfikacji

| Plik | Oczekiwana zmiana |
|---|---|
| `app/medidesk_client.py` | POST tylko na UUID; usunięcie pętli `candidates` + `resolve_submit_form_id()`; korekta docstringów o 500/webFormId |
| `tests/test_api.py` | usunięcie `TestResolveSubmitFormId`; (opc.) test POST-u na UUID |
| `docs/CHANGELOG.md` | wpis o zmianie wysyłki |
| `docs/captcha_diagnoza.md` | korekta wiersza o webFormId (linia ~49) |

### Kryteria akceptacji

- [x] `submit_form_urlencoded` wykonuje **dokładnie jeden** POST — na `form_id` (UUID); brak odniesień do webFormId w ścieżce POST. (Potwierdzone testem `TestSubmitPostsToUuid` + diff.)
- [x] `pytest` **bez regresji**: baseline `7 failed / 26 passed / 12 errors` → po zmianie `7 failed / 25 passed / 12 errors`. Delta = zamiana 2 testów `resolve` na 1 test UUID; **zero nowych failures**. Czerwone testy są pre-existing (env-mismatch repo „testowy", patrz Znane problemy).
- [ ] ⏳ **Walidacja baseline (QA) — ODŁOŻONA NA DEPLOY:** lokalnie niewykonalna (brak `MEDIDESK_DEBUG_TOKEN`, brak klucza CapSolver, lokalny Python nie weryfikuje cert SSL MD). Do wykonania po deployu na Render: `/debug/send?action=submit` → oczekiwane `medidesk_status: 200`. 500 → STOP/eskalacja.
- [x] `docs/CHANGELOG.md` zaktualizowany.
- [x] 🛡 **SecGate**: PASS — raport w `.agents/security_reports/integrator_wo004_uuid_only_submit.md`
- [x] 📝 **DocGate**: PASS — raport w `.agents/doc_reports/integrator_wo004_uuid_only_submit.md`

### Ograniczenia

- Zachowaj kompatybilność z Python 3.14 (Render) i Starlette (`render_template` nie dotyczy tej zmiany).
- Zachowaj istniejące komentarze „dlaczego" poza tymi błędnymi o UUID/500.
- Strict scope: tylko pliki wymienione wyżej.

### Notatki

- Blast radius (zweryfikowany): `resolve_submit_form_id` używane wyłącznie w `submit_form_urlencoded` (medidesk_client.py:187) + w testach (test_api.py:163-183). `submit_form_urlencoded` wołane z `app/webhook.py:459`, `app/main.py:148` (`/debug/send`), `app/main.py:194` (`/api/submit/{id}`) — wszystkie przekazują UUID jako `form_id`, więc brak zmian po stronie wywołujących.
- Walidacja decydująca: po zmianie `/debug/send` → `medidesk_status`. 200 = potwierdza diagnozę użytkownika (UUID poprawny). 500 = przeczy → STOP i eskalacja.
- Po deployu na Render: smoke `/login`, `/dashboard`, `/api/info`.

---

**Status**: 🔄 W trakcie — implementacja + SecGate + DocGate PASS; QA live-walidacja odłożona na deploy (Render)
