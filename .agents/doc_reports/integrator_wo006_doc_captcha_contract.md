# 📝 DocGate — WO#006 Dokumentacja: aktualny kontrakt captchy

**Data**: 2026-06-03
**Audytor**: 📝 Documentation Keeper
**Werdykt**: ✅ **PASS**

## Spójność dokumentacji

| Dokument | Stan | Uwagi |
|---|---|---|
| `docs/captcha_diagnoza.md` | ✅ | Baner „AKTUALNY KONTRAKT" na górze: aktualne (`enterprise-recaptcha-response`, `6Ldo-f0s…`) nadrzędne nad PDF (`captcha-response`, `6Lfs81gh…`). Sekcje 0–4 oznaczone jako historia. |
| `docs/README.md` | ✅ | Endpoint POST `{webFormId}` → `{formTemplateId}` (UUID); dopisane, że `enterprise-recaptcha-response` jest aktualny, a PDF podaje stary `captcha-response`. |
| `pliki od medidesk/_UWAGA-aktualnosc-captcha.md` | ✅ Nowy | Notatka, że sekcja reCAPTCHA w PDF jest nieaktualna; tabela stare↔aktualne; co w PDF nadal aktualne (endpoint UUID, format body, 500=token). |
| `docs/CHANGELOG.md` | ✅ | Wpis WO#006. |

## Spójność z kodem/ENV

- Zgodne z `app/config.py`: `captcha_header` default `enterprise-recaptcha-response`, `recaptcha_site_key` env-driven. **Kodu nie zmieniano** — wartości to ENV (zarządza użytkownik).
- Endpoint w docs = UUID (`formTemplateId`) — zgodne z `medidesk_client.submit_form_urlencoded` po WO#004.

## Rozbieżności rozwiązane

- README nie pokazuje już `{webFormId}` jako endpointu POST (był stały błąd po WO#004).
- Czytelnik PDF-a jest ostrzeżony notatką, że sekcja reCAPTCHA jest stara → koniec ryzyka „naprawiania wstecz" wg PDF.

## Wniosek

Dokumentacja spójna, aktualny kontrakt jednoznaczny i nadrzędny nad starym PDF. **DocGate: PASS.** SecGate: N/D (brak kodu).
