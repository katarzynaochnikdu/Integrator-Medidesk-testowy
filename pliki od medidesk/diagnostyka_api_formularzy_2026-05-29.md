# Diagnostyka API formularzy Medidesk - 2026-05-29

Cel dokumentu: opisac, jakie wywolania wykonujemy do API formularzy Medidesk, na jakich danych formularza pracujemy oraz jakie odpowiedzi otrzymujemy. Analiza dotyczy wylacznie komunikacji `Integrator -> Medidesk`, bez Facebooka.

## 1. Formularz testowy minimalny

Nowo utworzony formularz testowy:

- `formTemplateId`: `e8342a6a-b31a-4e2c-82be-146b73fe8457`
- `webFormId`: `kochnikmini`
- `name`: `kochnikmini`
- `clientId`: `f78acdda-f930-433e-a592-835808bfd700`
- `reCAPTCHA_site_key` podany w dokumentacji: `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`

Pobranie definicji:

```http
GET https://app.medidesk.io/api/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
Accept: application/json
```

Odpowiedz `200 OK`, skrot istotnych danych:

```json
{
  "formTemplateId": "e8342a6a-b31a-4e2c-82be-146b73fe8457",
  "webFormId": "kochnikmini",
  "name": "kochnikmini",
  "clientId": "f78acdda-f930-433e-a592-835808bfd700",
  "fields": [
    {
      "id": "71fa08d9-09b9-4a20-a172-bdaf1bdd020c",
      "type": "TEXT_FIELD",
      "fieldId": "string",
      "required": true,
      "name": "string"
    },
    {
      "id": "afe2f0d3-c79c-4221-a624-b27d265dd64c",
      "type": "EMAIL",
      "fieldId": "email",
      "required": true,
      "name": "email"
    }
  ]
}
```

Wniosek: formularz istnieje, API `GET` dziala, znamy wymagane pola.

## 2. Test backend-to-backend bez reCAPTCHA

Zgodnie z dokumentacja `POST` jest opisany jako:

```http
POST https://app.medidesk.io/api/forms/{formTemplateId}
```

Wykonalismy test backendowy na `formTemplateId`:

```http
POST https://app.medidesk.io/api/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: application/json, text/plain, */*
User-Agent: MedideskIntegrator/2.0 (+https://md-integrator-v1.onrender.com)
X-Requested-With: XMLHttpRequest
```

Body:

```text
siteDomain=integrator-xgih.onrender.com
siteUrl=/webhook/facebook
fieldsValues[string]=Backend to backend diag 20260529
fieldsValues[email]=diag.backend.to.backend@example.com
```

Faktyczna odpowiedz:

```http
HTTP 500 Internal Server Error
```

Body:

```json
{
  "timestamp": "2026-05-29T15:13:00.333+00:00",
  "status": 500,
  "error": "Internal Server Error",
  "path": "/api/forms/web-form/e8342a6a-b31a-4e2c-82be-146b73fe8457"
}
```

Wedlug dokumentacji, jesli problemem jest brak lub niepoprawna reCAPTCHA, API powinno zwrocic:

```http
HTTP 401 Unauthorized
```

Wniosek: `POST` na `formTemplateId` konczy sie bledem serwera `500`, mimo ze dokumentacja opisuje taki endpoint. Wyglada to tak, jakby backend Medidesk wewnetrznie przekierowywal request do `/api/forms/web-form/{id}`, ale traktowal `formTemplateId` jako identyfikator web-forma.

## 3. Test backend-to-backend na webFormId

Poniewaz `GET` zwraca `webFormId=kochnikmini`, wykonano analogiczny test na:

```http
POST https://app.medidesk.io/api/forms/kochnikmini
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: application/json, text/plain, */*
User-Agent: MedideskIntegrator/2.0 (+https://md-integrator-v1.onrender.com)
X-Requested-With: XMLHttpRequest
```

Body:

```text
siteDomain=integrator-xgih.onrender.com
siteUrl=/webhook/facebook
fieldsValues[string]=Backend to backend diag 20260529
fieldsValues[email]=diag.backend.to.backend@example.com
```

Faktyczna odpowiedz:

```http
HTTP 401 Unauthorized
```

Body: puste.

Wniosek: endpoint z `webFormId` zachowuje sie zgodnie z dokumentacja w zakresie autoryzacji reCAPTCHA, tj. brak tokenu daje `401`, a nie `500`. To sugeruje, ze do zapisu nalezy uzywac `webFormId`, mimo ze dokumentacja pokazuje `formTemplateId` w URL `POST`.

## 4. Test z reCAPTCHA v3 na webFormId

Wykonano test z tokenem reCAPTCHA v3 wygenerowanym przez przegladarke na stronie:

```text
https://app.medidesk.io/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
```

Uzyty site key:

```text
6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk
```

Generowanie tokenu:

```javascript
grecaptcha.execute("6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk", { action: "submit" })
```

Token zostal wygenerowany poprawnie. Dlugosc tokenu w testach: ok. `1408` znakow.

Nastepnie wykonano:

```http
POST https://app.medidesk.io/api/forms/kochnikmini
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: application/json, text/plain, */*
captcha-response: <token wygenerowany przez grecaptcha.execute>
X-Requested-With: XMLHttpRequest
```

Body:

```text
siteDomain=app.medidesk.io
siteUrl=/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
fieldsValues[string]=Diag kochnikmini 2026-05-29 17:05
fieldsValues[email]=diag.kochnikmini@example.com
```

Faktyczna odpowiedz:

```http
HTTP 401 Unauthorized
```

Body: puste.

Wykonano rowniez wariant JSON:

```http
POST https://app.medidesk.io/api/forms/kochnikmini
Content-Type: application/json
Accept: application/json, text/plain, */*
captcha-response: <token wygenerowany przez grecaptcha.execute>
```

Body:

```json
{
  "siteDomain": "app.medidesk.io",
  "siteUrl": "/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457",
  "attachments": {},
  "fieldsValues": {
    "string": "Diag kochnikmini JSON 2026-05-29 17:05",
    "email": "diag.kochnikmini.json@example.com"
  }
}
```

Faktyczna odpowiedz:

```http
HTTP 401 Unauthorized
```

Body: puste.

Wniosek: przy minimalnym formularzu, poprawnych wymaganych polach, poprawnym `webFormId` i tokenie reCAPTCHA wygenerowanym z podanego `site_key`, API nadal odrzuca request kodem `401`.

## 5. Formularz produkcyjny - dla porownania

Formularz produkcyjny uzywany w integratorze:

- `formTemplateId`: `d908ee01-0b7d-44a0-a494-a707ab5a55ef`
- `webFormId`: `Formularz-kontaktowy-KOCHNIKA`
- `name`: `Formularz kontaktowy KOCHNIKA`
- `clientId`: `f78acdda-f930-433e-a592-835808bfd700`

Istotne pola:

```text
Imie-i-nazwisko  TEXT_AREA   required=true
Mail             EMAIL       required=true
Telefon          PHONE       required=true
zgoda            CHECKBOX    required=true
Nazwa-kampanii   TEXT_FIELD  required=true
Nazwa-formularza TEXT_FIELD  required=true
FB-Lead-ID       TEXT_FIELD  required=true
```

Zaobserwowane zachowanie:

- `POST /api/forms/d908ee01-0b7d-44a0-a494-a707ab5a55ef` zwraca `500`.
- `POST /api/forms/Formularz-kontaktowy-KOCHNIKA` bez reCAPTCHA zwraca `401`.
- `POST /api/forms/Formularz-kontaktowy-KOCHNIKA` z tokenem reCAPTCHA wygenerowanym przez `grecaptcha.execute(...)` rowniez zwraca `401`.

## 6. Aktualny wniosek techniczny

Po naszej stronie request jest budowany zgodnie z dokumentacja:

- pobieramy definicje przez `GET /api/forms/{formTemplateId}`;
- odczytujemy `webFormId`;
- wysylamy wymagane `fieldsValues`;
- wysylamy `siteDomain` i `siteUrl`;
- dla testu z reCAPTCHA wysylamy naglowek `captcha-response`;
- testowalismy oba formaty body dopuszczone w dokumentacji: `application/x-www-form-urlencoded` i `application/json`.

Wyniki wskazuja na dwa problemy po stronie kontraktu/API Medidesk:

1. `POST` na dokumentowany `formTemplateId` zwraca `500`, mimo ze przy problemie reCAPTCHA powinien zwracac `401`.
2. `POST` na `webFormId` z tokenem reCAPTCHA wygenerowanym z podanego `site_key` zwraca `401`, czyli token jest odrzucany przez backend Medidesk.

## 7. Prosba do Medidesk o sprawdzenie

Prosimy sprawdzic po stronie backendu Medidesk:

1. Czy `POST /api/forms/{formTemplateId}` jest nadal poprawnym endpointem zgodnie z dokumentacja, czy dla zapisu nalezy uzywac `webFormId`.
2. Dlaczego `POST /api/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457` zwraca `500`, zamiast dokumentacyjnego `401`.
3. Czy `reCAPTCHA_site_key` `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk` jest aktywnie sparowany po stronie Medidesk z prawidlowym secret key.
4. Dla jakiej domeny/hostname backend Medidesk oczekuje tokenu reCAPTCHA v3:
   - `app.medidesk.io`
   - domena placowki
   - domena integratora `integrator-xgih.onrender.com`
   - inna domena
5. Czy backend Medidesk wymaga konkretnej akcji reCAPTCHA v3 innej niz `{ action: "submit" }`.
6. Czy dla integracji backend-to-backend istnieje oficjalny bypass/API key/whitelist, poniewaz reCAPTCHA v3 jest mechanizmem przegladarkowym, a historycznie integracja dzialala server-to-server.

## 8. Minimalny request do odtworzenia

Endpoint:

```http
POST https://app.medidesk.io/api/forms/kochnikmini
```

Headers:

```http
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: application/json, text/plain, */*
captcha-response: <token z grecaptcha.execute dla site key 6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk>
X-Requested-With: XMLHttpRequest
```

Body:

```text
siteDomain=app.medidesk.io
siteUrl=/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
fieldsValues[string]=Diag kochnikmini
fieldsValues[email]=diag.kochnikmini@example.com
```

Oczekiwane wedlug dokumentacji:

```http
HTTP 200 OK
```

Faktyczne:

```http
HTTP 401 Unauthorized
```

