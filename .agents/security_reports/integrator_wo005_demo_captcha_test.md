# 🛡 SecGate — WO#005 Test captchy na /demo/contact

**Data**: 2026-06-03
**Audytor**: 🛡 Security
**Zakres diffa**: `app/templates/demo_contact.html`, `docs/CHANGELOG.md`
**Werdykt**: ✅ **PASS**

## Co zmieniono

- Klienckie (JS) dodanie przycisku „Test captcha" + naprawa danych presetów (`PEOPLE`). **Zero zmian po stronie serwera** (`main.py`, `medidesk_client.py` nietknięte).

## Checklista

| Wektor | Ocena | Uwagi |
|---|---|---|
| Sekrety | ✅ Bez zmian | Brak sekretów w diffie. `BAD_TOKEN = "INVALID_TOKEN_CAPTCHA_TEST"` to nieszkodliwa stała-zaślepka, nie sekret. Site-key nadal z `{{ recaptcha_site_key }}` (publiczny). |
| Auth / gating | ✅ Bez zmian | Strona dalej za `demo_page_enabled`. Używa istniejącego, otwartego `/api/submit/{id}` — nie dodaje nowego endpointu ani nie zmienia gatingu. |
| Nowa powierzchnia ataku | ✅ Brak | `/api/submit` istniał i był otwarty; test tylko woła go z przeglądarki. Nic serwerowego nie dochodzi. |
| XSS | ✅ Bez regresji | Render pól bez zmian wzorca (ten sam string-concat co wcześniej). Werdykt wstawiany przez `textContent` (nie `innerHTML`) — brak iniekcji. |
| Ruch do Medideska | ℹ️ Świadome | Jeden klik testu = 2 POST-y (zły+dobry token) → do 2 leadów testowych. Użytkownik zaakceptował („testówka może sobie wysyłać"). Strona diagnostyczna, gated. |

## Wniosek

Zmiana czysto kliencka, bez sekretów, bez zmian auth/serwera, werdykt przez `textContent`. **SecGate: PASS.**
