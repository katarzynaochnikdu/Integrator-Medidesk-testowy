# Integracja z Medidesk — jak wysyłać leady (specyfikacja wdrożeniowa)

> **Plik kanoniczny do przekazania.** Opisuje dokładnie to, co testujemy i co działa.
> Ma **pierwszeństwo nad** `Medidesk - Formularze - Specyfikacja API.pdf` w części
> reCAPTCHA (PDF jest w tym zakresie nieaktualny).
>
> Wersja: 2026-06-03 · Działająca referencja na żywo: **https://md-integrator-old.onrender.com/demo/contact**

---

## 1. Skrót — jak to działa

Formularz Medideska wysyła się **jednym POST-em na UUID formularza** (`formTemplateId`),
z **tokenem reCAPTCHA** w nagłówku. Pola formularza pobiera się wcześniej przez GET.

- **GET** `https://app.medidesk.io/api/forms/{formTemplateId}` → definicja pól (ich `fieldId`/`type`/`required`).
- **POST** `https://app.medidesk.io/api/forms/{formTemplateId}` → wysłanie danych (z tokenem captcha).
- `{formTemplateId}` to **UUID** (np. `e8342a6a-b31a-4e2c-82be-146b73fe8457`).
  **NIE używać** `webFormId` ani „string" — niezgodne z dokumentacją.

**Reguła odpowiedzi:** poprawny strzał = **UUID + poprawnie wygenerowany token**.
**HTTP 500 = brak lub niepoprawny token** (Medidesk oddaje 500 zamiast 401).

---

## 2. Aktualne wartości (NADRZĘDNE nad starym PDF)

| Element | AKTUALNE (stosować) | Stare z PDF (NIE używać) |
|---|---|---|
| Nagłówek tokenu captcha | **`enterprise-recaptcha-response`** | `captcha-response` |
| reCAPTCHA site-key | **`6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`** | `6Lfs81ghAAAAAL1x7coNFL3OORZHAkNk7ugPcBJ_` |
| Typ reCAPTCHA | Enterprise (reCAPTCHA v3) | zwykła v3 |
| `action` reCAPTCHA | `submit` | — |

---

## 3. Krok po kroku

### 3.1. Pobierz definicję formularza (raz, na etapie wdrożenia)

```http
GET https://app.medidesk.io/api/forms/{formTemplateId}
Accept: application/json
```

Zwraca m.in. tablicę `fields` z `fieldId`, `type` (PHONE/EMAIL/TEXT_FIELD/TEXT_AREA/CHECKBOX/SELECT/ATTACHMENTS), `required`. Z tego znasz nazwy pól (`fieldId`) potrzebne w POST.

### 3.2. Wygeneruj token reCAPTCHA

- **Przeglądarka (user wypełnia formularz):** załaduj reCAPTCHA Enterprise z site-keyem i wywołaj `grecaptcha.enterprise.execute(SITE_KEY, { action: "submit" })`. Token jest jednorazowy i krótko żyje.
- **Server-to-server (np. webhook bez przeglądarki):** użyj solvera (np. CapSolver) z residential IP — token z datacenter IP dostaje niski score i bywa odrzucany.

### 3.3. Wyślij POST na UUID

```http
POST https://app.medidesk.io/api/forms/{formTemplateId}
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: application/json, text/plain, */*
enterprise-recaptcha-response: <TOKEN_Z_reCAPTCHA>
```

Body (urlencoded). `fieldId` jako klucz w `fieldsValues[...]`; wartości URL-encoded; **CHECKBOX = `true`/`false`**:

```text
siteDomain=app.medidesk.io
siteUrl=/forms/{formTemplateId}
fieldsValues[string]=Jan Testowy
fieldsValues[email]=jan.test@example.com
fieldsValues[zgoda]=true
```

> Dozwolony też `Content-Type: application/json` z body
> `{ "siteDomain", "siteUrl", "attachments": {}, "fieldsValues": { "<fieldId>": "<value>" } }`.

### 3.4. Zinterpretuj odpowiedź

| Kod | Znaczenie |
|---|---|
| **200** (puste body) | OK — lead przyjęty. |
| **400** | Błędy walidacji. Body JSON: `globalErrors` / `fieldErrors` (`required`, `minLength`, `maxLength`, `format`). |
| **500** | **Brak lub niepoprawny token reCAPTCHA** (Medidesk oddaje 500 zamiast dokumentacyjnego 401). |

---

## 4. Konkretny przykład (formularz testowy `kochnikmini`)

`formTemplateId = e8342a6a-b31a-4e2c-82be-146b73fe8457` · pola: `string` (TEXT_FIELD, wymagane), `email` (EMAIL, wymagane), `zgoda` (CHECKBOX).

```http
POST https://app.medidesk.io/api/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
enterprise-recaptcha-response: <token z grecaptcha.enterprise.execute dla 6Ldo-f0s...>

siteDomain=app.medidesk.io&siteUrl=/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457&fieldsValues[string]=Jan%20Testowy&fieldsValues[email]=jan.test%40example.com&fieldsValues[zgoda]=true
```

Formularz produkcyjny (dla porównania): `formTemplateId = d908ee01-0b7d-44a0-a494-a707ab5a55ef`.

---

## 5. Nasza implementacja referencyjna (do podejrzenia / skopiowania)

- **Na żywo (działa, wysyła realne leady):** https://md-integrator-old.onrender.com/demo/contact — ma przycisk **„Test captcha: zły token → dobry token"**, który pokazuje, czy Medidesk weryfikuje captchę i czy token przechodzi.
- **Kod przeglądarkowy (grecaptcha + POST):** `app/templates/demo_contact.html`.
- **Kod server-to-server (budowa body, nagłówki, solver):** `app/medidesk_client.py` (`submit_form_urlencoded`, `build_urlencoded_body`) + `app/captcha_provider.py`.
- **Pełny kontrakt + historia diagnozy:** `docs/captcha_diagnoza.md` (sekcja „AKTUALNY KONTRAKT").

---

## 6. Konfiguracja (u nas — zmienne środowiskowe)

Wartości captchy trzymamy w ENV (zmiana = zmiana zmiennej, bez ruszania kodu):

| Zmienna | Wartość u nas |
|---|---|
| `MEDIDESK_CAPTCHA_HEADER` | `enterprise-recaptcha-response` |
| `MEDIDESK_RECAPTCHA_SITE_KEY` | `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk` |
| `MEDIDESK_CAPTCHA_ACTION` | `submit` |
| `MEDIDESK_CAPTCHA_ENTERPRISE` | (wg ustawienia po stronie Medideska) |

---

## 7. Czego NIE robić

- ❌ POST na `webFormId` lub „string" zamiast UUID — niezgodne z dokumentacją.
- ❌ Trzymać się sekcji reCAPTCHA ze starego PDF (`captcha-response`, klucz `6Lfs81gh...`) — nieaktualne.
- ❌ Traktować 500 jako „zły endpoint" — to objaw braku/niepoprawnego tokenu.
