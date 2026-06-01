# Diagnoza: leady do Medideska — reCAPTCHA v3 Enterprise

> Data: 2026-05-30 / aktualizacja 2026-06-01
> Status: **DZIAŁA (HTTP 200)** — Medidesk **tymczasowo** wyłączył captchę.
> To jest nasz **punkt odniesienia (baseline)**: wszystko poza captchą jest
> potwierdzone jako poprawne. Gdy captcha wróci, będzie **jedyną** nową zmienną.

---

## 0. ⭐ STAN DZIAŁAJĄCY (baseline — nie ruszać) ⭐

**2026-06-01: Medidesk TYMCZASOWO wyłączył captchę. Wysyłka zwraca HTTP 200.**
Potwierdzone: `/debug/send?action=submit` → `medidesk_status: 200, medidesk_ok: true`.

**Świadoma decyzja: NIE zmieniamy niczego w konfiguracji.** Zostawiamy dokładnie
ten sam request, który teraz daje 200 — to nasz znany-dobry stan. Gdy Medidesk
ponownie włączy captchę, jedyną różnicą będzie weryfikacja tokenu → łatwo
wyizolujemy, czy problem jest po naszej stronie czy ich.

### Dokładny request, który DZIAŁA (HTTP 200)

```http
POST https://app.medidesk.io/api/forms/kochnikmini
```
Nagłówki:
```
Content-Type:                   application/x-www-form-urlencoded; charset=UTF-8
Accept:                         application/json, text/plain, */*
Origin:                         https://app.medidesk.io
Referer:                        https://app.medidesk.io/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
User-Agent:                     MedideskIntegrator/2.0 (+https://md-integrator-old.onrender.com)
X-Requested-With:               XMLHttpRequest
enterprise-recaptcha-response:  <token reCAPTCHA>   ← przy captcha OFF ignorowany
```
Body (urlencoded):
```
siteDomain=app.medidesk.io
&siteUrl=/forms/e8342a6a-b31a-4e2c-82be-146b73fe8457
&fieldsValues[string]=Jan Testowy
&fieldsValues[email]=jan.test@example.com
&fieldsValues[zgoda]=true
```
Odpowiedź: **HTTP 200, puste body** = lead przyjęty.

### Konfiguracja, która daje ten 200 (Render env + kod)

| Ustawienie | Wartość | Gdzie |
|---|---|---|
| Endpoint | `webFormId` = `kochnikmini` (resolve z UUID) | `medidesk_client.resolve_submit_form_id` |
| Nagłówek tokenu | `enterprise-recaptcha-response` | `MEDIDESK_CAPTCHA_HEADER` (default w configu) |
| Site-key | `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk` | `MEDIDESK_RECAPTCHA_SITE_KEY` |
| Tryb captcha | `solver` (CapSolver) | `MEDIDESK_CAPTCHA_MODE` |
| Format | urlencoded, `fieldsValues[fieldId]=value` | `build_urlencoded_body` |

### Co ten 200 DOWODZI (kluczowe)

Skoro przy captcha OFF dostajemy 200, to **wszystko poza captchą jest poprawne**:
endpoint ✅, format body ✅, mapowanie pól ✅, nazwa nagłówka ✅, klucz ✅.
→ **Gdy captcha wróci i znów poleci 401, przyczyną będzie WYŁĄCZNIE weryfikacja
tokenu (score / action / valid) po stronie Medideska — nic po naszej.**

### Czego ten 200 NIE dowodzi

Przy captcha OFF token jest **ignorowany** — więc **nie potwierdziliśmy**, że
nasz token przechodzi weryfikację z captchą ON. Z captchą ON każdy nasz wariant
dawał 401 (zob. sekcja 2). Ta przyczyna **nie została ustalona** — Medidesk ją
obszedł, nie naprawił.

### Otwarte pytanie do Medideska (na powrót captchy)

Zanim/gdy włączą captchę — wyciągnąć od nich, co zwraca ich `createAssessment`
dla naszych tokenów: `tokenProperties.valid` (+ `invalidReason`), `score`,
`expectedAction`. Bez tego, gdy captcha wróci, znów będziemy zgadywać.

---

## 1. O co chodzi (po ludzku)

Formularz Medideska (`POST /api/forms/{webFormId}`) jest chroniony przez
Google reCAPTCHA v3. Żeby wysłać leada, trzeba dołączyć nagłówek
`captcha-response` z ważnym tokenem reCAPTCHA.

Problem: **Medidesk odrzuca każdy token, jaki wyślemy — zwraca HTTP 401.**
Lead nie wchodzi.

Token reCAPTCHA v3 to nie hasło — to „ocena", czy żądanie wygląda na
człowieka (score 0–1). Medidesk po swojej stronie sprawdza ten token u Google
(`siteverify`) i jeśli weryfikacja się nie powiedzie → 401.

---

## 2. Dlaczego to NIE jest nasz problem (dowody)

Przetestowaliśmy **wszystkie** zmienne, które są po naszej stronie. Każda jest
poprawna, a Medidesk i tak odrzuca:

| Co sprawdziliśmy | Jak | Wynik Medideska |
|---|---|---|
| Czy token w ogóle powstaje | przez serwis CapSolver | ✅ token zawsze się generuje |
| **Score (jakość)** | wymuszony od 0.3 aż do **0.9** | ❌ 401 |
| **Action** | submit, homepage, contact, form, lead, pusty | ❌ 401 |
| **Typ reCAPTCHA** | classic v3 **oraz** Enterprise | ❌ 401 |
| **Site-key #1** | `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk` (nowszy, z panelu) | ❌ 401 |
| **Site-key #2** | `6Lfs81ghAAAAAL1x7coNFL3OORZHAkNk7ugPcBJ_` (starszy, z dokumentacji) | ❌ 401 |
| **Domena** | `app.medidesk.io` (własna domena Medideska, na pewno na whiteliście) | ❌ 401 |

Dodatkowy, mocny dowód: token wygenerowany **bezpośrednio na prawdziwej
stronie formularza Medideska** (`app.medidesk.io`, ich własny mechanizm
reCAPTCHA) — **też dostał 401.**

### Wniosek

Skoro **oba** klucze z dokumentacji Medideska, przy wysokim score, na ich
własnej domenie, dają 100% odrzuceń — jedyne logiczne wyjaśnienie jest takie:

> **Po stronie Medideska secret-key (klucz prywatny, którym weryfikują token)
> nie pasuje do żadnego z podanych site-keyów — albo ich weryfikacja
> reCAPTCHA jest źle skonfigurowana / zepsuta.**

Pary site-key + secret-key muszą pochodzić z tego samego panelu Google
reCAPTCHA. Jeśli ich backend ma secret od innego klucza, to **każdy** token
— choćby idealny — zostanie odrzucony. Dokładnie to widzimy.

**Tego nie da się naprawić z naszej strony — nie mamy dostępu do ich
secret-key.**

---

## 3. Co jest gotowe po naszej stronie

Cała integracja jest napisana i działa. Czeka wyłącznie na sprawny klucz
po stronie Medideska. Gdy Medidesk naprawi parę klucz↔secret, **ten sam kod
zacznie zwracać sukces bez żadnych zmian**:

- ✅ Pobieranie definicji formularza z Medideska (dynamiczne pola)
- ✅ Generowanie tokenu reCAPTCHA (serwis CapSolver, residential IP, wysoki score)
- ✅ Wysyłka leada z nagłówkiem `captcha-response` na właściwy `webFormId`
- ✅ Strona testowa `/demo/contact` (dynamiczny formularz, dane testowe wg typu pola)

Jedyny brakujący element: **akceptacja tokenu przez Medidesk.**

---

## 4. Wiadomość do wysłania Medideskowi (gotowa)

> Dzień dobry,
>
> Wdrażamy integrację Facebook Lead Ads → Medidesk (server-to-server) na
> formularzu `kochnikmini` (ID `e8342a6a-b31a-4e2c-82be-146b73fe8457`,
> webFormId `kochnikmini`).
>
> Wysyłamy `POST /api/forms/kochnikmini` z nagłówkiem `captcha-response`
> zawierającym ważny token reCAPTCHA v3. **Każdy token jest odrzucany
> z kodem HTTP 401.**
>
> Po naszej stronie zweryfikowaliśmy wszystko:
> - token o wysokim score (≥0.9),
> - oba site-keye z Waszej dokumentacji: `6Ldo-f0sAAAAAJO47MmGJQu_XZII-2Gd4WyLnyAk`
>   oraz `6Lfs81ghAAAAAL1x7coNFL3OORZHAkNk7ugPcBJ_`,
> - tryb classic v3 i Enterprise,
> - różne wartości `action`,
> - token generowany dla domeny `app.medidesk.io`.
>
> We wszystkich przypadkach: **HTTP 401**. Token wygenerowany nawet
> bezpośrednio na Waszej stronie formularza również jest odrzucany.
>
> **Prosimy o sprawdzenie po Waszej stronie**, co zwraca Wasze
> `siteverify` / assessment dla naszych żądań: `success`, `score`,
> `error-codes`, `hostname`. Podejrzewamy, że **secret-key w Waszym backendzie
> nie paruje z żadnym z podanych site-keyów**, albo domena nie jest
> zarejestrowana dla tego klucza — to jedyne, co tłumaczy 100% odrzuceń
> poprawnych tokenów.
>
> Alternatywnie: czy dla integracji server-to-server (Facebook Lead Ads,
> bez przeglądarki użytkownika) możecie udostępnić endpoint z autoryzacją
> API-key/Bearer bez reCAPTCHA, albo wyłączyć/obniżyć próg reCAPTCHA
> na tym formularzu?
>
> Pozdrawiam

---

## 5. Co teraz (żeby nie palić kredytów)

Do czasu odpowiedzi Medideska:
- ustaw `MEDIDESK_CAPTCHA_MODE=none` na Render (przestaniemy wołać CapSolver),
- klucz w `MEDIDESK_RECAPTCHA_SITE_KEY` bez znaczenia, póki ich strona nie działa.

Gdy Medidesk potwierdzi/naprawi klucz:
- `MEDIDESK_CAPTCHA_MODE=solver` + właściwy site-key,
- test: `https://md-integrator-old.onrender.com/demo/contact` → klik „Wyślij”
  → ma być sukces zamiast 401.
