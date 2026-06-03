# 📝 DocGate — WO#007 Specyfikacja wdrożeniowa do przekazania

**Data**: 2026-06-03
**Audytor**: 📝 Documentation Keeper
**Werdykt**: ✅ **PASS**

## Zawartość `docs/INTEGRACJA_MEDIDESK.md`

| Sekcja | Stan |
|---|---|
| Skrót działania (GET + POST na UUID, 500=token) | ✅ |
| Aktualne wartości vs stare PDF (header, site-key, typ) | ✅ |
| Krok po kroku (definicja → token → POST → odpowiedź) | ✅ |
| Konkretny przykład `kochnikmini` (e8342a6a) — 1:1 z demo | ✅ |
| Referencja na żywo `/demo/contact` + pliki kodu | ✅ |
| ENV + „czego NIE robić" | ✅ |

## Spójność

- Endpoint = UUID (`formTemplateId`) — zgodne z `medidesk_client` po WO#004 i z WO#006.
- Captcha = `enterprise-recaptcha-response` + `6Ldo-f0s…` — zgodne z aktualnym kontraktem (WO#006), nadrzędne nad PDF.
- Przykład `e8342a6a` zgodny z domyślnym `default_form_id` na `/demo/contact` (`app/main.py:34`).
- Bez zmian w kodzie/configu.

## Wniosek

Dokument samodzielny, aktualny, gotowy do przekazania. **DocGate: PASS.** SecGate: N/D.
