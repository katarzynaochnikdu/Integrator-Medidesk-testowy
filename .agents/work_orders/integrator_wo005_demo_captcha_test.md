# 📋 Work Order #005

**Data**: 2026-06-03
**Worker**: ⚙️ Implementer → 🛡 Security → 📝 Doc Keeper
**Priorytet**: 🟡 Normalny
**Snapshot**: `przed_demo_captcha_test_20260603`

### Cel

Na stronie testowej `/demo/contact`: (1) dodać test captchy „zły token → dobry token" pokazujący oba wyniki + werdykt (czy MD weryfikuje captchę i czy nasz token przechodzi); (2) naprawić niespójne dane testowe (klik „Marek Zieliński" wstawiał dane Anny).

### Kontekst

Użytkownik chce na testówce sprawdzić „czy przechodzę captchę". Samo 200 z demo tego nie mówi — demo zawsze dosyła token. Potrzebne porównanie: wysyłka bez ważnego tokenu vs z ważnym tokenem.

**Subtelność:** `/api/submit/{id}` przy braku tokenu **sam woła solver** (`submit_form_urlencoded` → `get_captcha_token`). Więc „całkiem bez tokenu" z klienta mógłby polecieć z tokenem dociągniętym serwerowo. Rozwiązanie **bez zmian serwera**: szot 1 wysyła **zaślepkę** (`captchaResponse` = stały zły token) — serwer ją przekazuje (nie woła solvera, bo token jest „obecny"), a MD odrzuca ją jeśli weryfikuje. Diagnostycznie równoważne „bez tokenu".

**Bug danych:** przyciski presetów `["Anna Nowak","Marek Zieliński","Ewa Kowalczyk"]` (idx 0/1/2), ale pula `FAKE.TEXT_FIELD[0]=["Jan Kowalski","Anna Nowak","Marek Zieliński"]` i `FAKE.EMAIL=["jan…","anna…","marek…"]` → `prefill(1)` (Marek) wstawia `pool[1]="Anna Nowak"` + `EMAIL[1]="anna…"`. Stąd „Marek → Anna".

### Zakres

**W zakresie (DO)**:
- [ ] `app/templates/demo_contact.html` — pojedyncze źródło prawdy `PEOPLE` (name/email/phone/subject/address/note), z którego idą i przyciski presetów, i `prefill()`. Naprawia przesunięcie indeksów.
- [ ] `app/templates/demo_contact.html` — przycisk „Test captcha: zły token → dobry token". Wykonuje 2 POST-y na `/api/submit/{id}`: (1) z zaślepką `captchaResponse`, (2) z prawdziwym tokenem enterprise. Pokazuje oba statusy + werdykt:
  - zły=200 → captcha OFF (oba przejdą; tokenu nie ma jak zweryfikować)
  - zły≠200, dobry=200 → captcha ON i token PRZECHODZI ✅
  - zły≠200, dobry≠200 → captcha ON, token ODRZUCONY ❌
  - zły=200, dobry≠200 → anomalia, pokaż surowe
- [ ] `docs/CHANGELOG.md` — wpis.

**Poza zakresem (NIE RÓB)**:
- NIE zmieniać serwera (`main.py`, `medidesk_client.py`) — rozwiązanie czysto klienckie (zaślepka tokenu).
- NIE ruszać configu captchy, nagłówków, ścieżki webhooka.
- NIE zmieniać istniejącego przycisku „Wyślij do Medidesk" (zostaje obok testu).

### Pliki do modyfikacji

| Plik | Oczekiwana zmiana |
|---|---|
| `app/templates/demo_contact.html` | `PEOPLE` source-of-truth + naprawiony `prefill`; przycisk i logika testu captchy; styl werdyktu |
| `docs/CHANGELOG.md` | wpis WO#005 |

### Kryteria akceptacji

- [x] Klik presetu „Marek Zieliński" wstawia dane Marka (nie Anny); analogicznie Anna/Ewa. (Naprawione `PEOPLE`; `prefill(1)` → Marek + marek.zielinski@…)
- [x] Przycisk testu robi 2 strzały i pokazuje czytelny werdykt (OFF / ON-przechodzi / ON-odrzucony). Składnia JS zweryfikowana (Node `vm.Script` ALL_OK).
- [x] Istniejący „Wyślij do Medidesk" działa jak wcześniej (zrefaktorowany na `collectBody`/`postLead`, zachowane zachowanie).
- [x] `docs/CHANGELOG.md` zaktualizowany.
- [x] 🛡 **SecGate**: PASS — `.agents/security_reports/integrator_wo005_demo_captcha_test.md`
- [x] 📝 **DocGate**: PASS — `.agents/doc_reports/integrator_wo005_demo_captcha_test.md`
- [ ] ⏳ Walidacja end-to-end (realne 2 strzały) — po stronie użytkownika w produkcji po deployu.

### Ograniczenia

- Zmiana wyłącznie w szablonie demo (gated `demo_page_enabled`). Weryfikacja końcowa w produkcji (lokalnie egress TLS blokuje MD — patrz Znane problemy / pamięć).
- Zachowaj istniejące komentarze „dlaczego" (enterprise token, action).

### Notatki

- Walidacja end-to-end: użytkownik na `/demo/contact` w produkcji po deployu.

---

**Status**: ✅ Wykonane — implementacja + SecGate + DocGate PASS (walidacja end-to-end user-side w produkcji)
