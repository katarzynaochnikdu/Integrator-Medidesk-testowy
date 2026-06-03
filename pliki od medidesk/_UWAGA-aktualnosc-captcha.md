# ⚠️ UWAGA — aktualność plików od Medideska

> Notatka NASZA (nie od Medideska). Dotyczy `Medidesk - Formularze - Specyfikacja API.pdf`.

**Sekcja „Google reCAPTCHA v3" w PDF-ie jest NIEAKTUALNA.** Późniejsza komunikacja
z Medideskiem (info z 2026-06-03) ustaliła inny, aktualny kontrakt captchy.

| Element | PDF (STARE) | Aktualne (stosujemy) |
|---|---|---|
| Nagłówek tokenu | `captcha-response` | **`enterprise-recaptcha-response`** |
| Site-key | `6Lfs81ghAAAAAL1x7coNFL3OORZHAkNk7ugPcBJ_` | **`6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`** |
| Typ | zwykła v3 | Enterprise |

**Aktualne wartości trzymamy w zmiennych środowiskowych** (`MEDIDESK_CAPTCHA_HEADER`,
`MEDIDESK_RECAPTCHA_SITE_KEY`, `MEDIDESK_CAPTCHA_ENTERPRISE`) — zmiana = zmiana ENV
na Render, bez ruszania kodu.

**Co w PDF-ie JEST nadal aktualne:** endpoint `POST /api/forms/{formTemplateId}`
(**UUID**), format body (`fieldsValues` + `siteDomain`/`siteUrl`, urlencoded lub JSON),
CHECKBOX `'true'/'false'`, oraz reguła: poprawny strzał = **UUID + token**, a **HTTP 500
= brak/niepoprawny token** (nie zły endpoint). `webFormId`/`string` w POST — niezgodne
z dokumentacją (patrz WO#004).

Pełny aktualny kontrakt: `docs/captcha_diagnoza.md` (sekcja „AKTUALNY KONTRAKT").
