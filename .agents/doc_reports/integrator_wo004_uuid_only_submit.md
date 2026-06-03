# 📝 DocGate — WO#004 Wysyłka tylko na UUID

**Data**: 2026-06-03
**Audytor**: 📝 Documentation Keeper
**Werdykt**: ✅ **PASS**

## Spójność dokumentacji

| Dokument | Stan | Uwagi |
|---|---|---|
| `docs/CHANGELOG.md` | ✅ Zaktualizowany | Nowy wpis „WO#004 Wysyłka tylko na UUID" (Zmienione / Usunięte / Naprawione), format Keep a Changelog PL. |
| `docs/captcha_diagnoza.md` | ✅ Zaktualizowany | Wiersz „Endpoint" zmieniony z webFormId/`resolve_submit_form_id` na **UUID / `submit_form_urlencoded`**; dodana notka korygująca WO#004 (500 = token, nie endpoint). |
| `CLAUDE.md` | ✅ Bez zmian (spójny) | Opis przepływu (linia 32): „`submit_form_urlencoded` POSTs to `…/api/forms/{id}`" — nadal poprawny (UUID = `{id}`). Nie wspominał o routingu webFormId, więc nic do korekty. |
| `.agents/context/integrator_project_context.md` | ✅ Bez zmian | `medidesk_client.py` nie figuruje w tabeli kluczowych plików; brak potrzeby zmian. |
| `.agents/context/integrator_system_state.md` | ✅ Zaktualizowany (Master, krok 6) | WO#004 przeniesiony do „Wykonane", dodany tag `przed_uuid_only_submit_20260603`, dopisana znana niespójność env repo + status live-walidacji. |

## Docstringi / komentarze w kodzie

- ✅ Docstring `submit_form_urlencoded` opisuje nowe zachowanie (UUID-only + rola tokenu, 500=token).
- ✅ Usunięto docstring `resolve_submit_form_id` (funkcja skasowana).
- ✅ Komentarz Origin/Referer pozbawiony obalonej teorii „web-form handler → 500"; zachowane uzasadnienie browser-parity.
- ✅ Komentarze „dlaczego" (UTF-8 fieldId, fallback siteDomain/siteUrl) zachowane.

## Uwaga (świadoma decyzja, nie błąd)

- Historyczny wpis w `CHANGELOG.md` (branch `feat/medidesk-captcha-bridge`): „Routing przez webFormId … POST na UUID wywala 500" **pozostawiony bez zmian** — zgodnie z konwencją Keep a Changelog historii się nie przepisuje. Nowy wpis WO#004 jawnie go zastępuje i prostuje diagnozę.

## Wniosek

Dokumentacja spójna z kodem po zmianie. **DocGate: PASS.**
