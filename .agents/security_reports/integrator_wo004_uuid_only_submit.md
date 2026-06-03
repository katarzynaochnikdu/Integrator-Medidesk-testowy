# 🛡 SecGate — WO#004 Wysyłka tylko na UUID

**Data**: 2026-06-03
**Audytor**: 🛡 Security
**Zakres diffa**: `app/medidesk_client.py`, `tests/test_api.py`, `docs/CHANGELOG.md`, `docs/captcha_diagnoza.md`
**Werdykt**: ✅ **PASS**

## Co zmieniono (z perspektywy bezpieczeństwa)

- `submit_form_urlencoded()` wykonuje teraz **jeden POST na UUID** zamiast pętli po dwóch identyfikatorach (webFormId + UUID).
- Usunięto `resolve_submit_form_id()` (wraz z jego wywołaniem `fetch_form_definition` per-submit).
- Skorygowano komentarze/docstringi; zmiany w dokumentacji.

## Checklista audytu

| Wektor | Ocena | Uwagi |
|---|---|---|
| Sekrety / klucze | ✅ Bez zmian | Żaden sekret nie dodany/usunięty. Site-key w `captcha_diagnoza.md` był wcześniej i jest **publicznym** kluczem reCAPTCHA (nie sekret). |
| Auth / gating | ✅ Bez zmian | `submit_form_urlencoded` wołane z webhooka (FB signature), `/api/submit`, `/debug/send` (debug-token, WO#003). Gating nietknięty. |
| SQL / DB | ✅ N/D | Brak interakcji z bazą w zmienionym kodzie. |
| XSS / szablony | ✅ N/D | Brak zmian w templatkach/HTML. |
| Tokeny | ✅ Bez regresji | Token captcha nadal w konfigurowalnym nagłówku. Log loguje `captcha=%s` jako **bool** (`bool(captcha_response)`), nie wartość tokenu — brak wycieku tokenu. |
| Powierzchnia ataku | ✅ **Zmniejszona** | Usunięto dodatkowy wychodzący POST (próba webFormId) oraz GET (`fetch_form_definition`) per-lead. Mniej żądań do MD, węższy kod. |
| Audit trail | ✅ N/D | Zmiana nie jest mutacją integracji — `_audit` nie dotyczy. |

## Obserwacja informacyjna (NIE blokuje WO#004)

- Log `WARNING` przy nieudanym POST loguje `sent_body` (urlencoded body z PII leada: imię/email/telefon) oraz `response` (body MD, ucięte do 600 zn.). **To zachowanie pre-existing** — istniało w pętli przed zmianą. Moja zmiana **zmniejsza** ekspozycję: body logowane raz i tylko przy porażce (wcześniej do 2× per submit). Rekomendacja na osobny WO: redakcja PII w logach diagnostycznych.

## Wniosek

Brak nowych findingów. Zmiana zawęża powierzchnię (mniej żądań do MD), nie dotyka auth/sekretów/DB, nie loguje tokenu. **SecGate: PASS.**
