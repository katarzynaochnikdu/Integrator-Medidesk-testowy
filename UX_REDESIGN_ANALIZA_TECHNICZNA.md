# Medidesk Integrator — Analiza techniczna dla UX
> Supplement do UX_REDESIGN.md · Co faktycznie działa pod spodem i jak to wpływa na UI

---

## 1. SESJA UŻYTKOWNIKA — jak naprawdę działa

### Co odkryłam

Sesja trwa **3 godziny** (sliding window — każda akcja przesuwa licznik).  
Przechowywana w SQLite, nie w pamięci — przeżywa restart serwera.  
Token przesyłany przez **cookie HTTP-only** (podpisane HMAC-SHA256), z fallbackiem na localStorage + nagłówek.

Token FB (long-lived) ważny **60 dni**. Tokeny stron Facebook (page tokens) — **nigdy nie wygasają**.

### Implikacje dla UX

**Co działa dobrze:**
- Sesja 3h to świadomy wybór (odnotowałam w pamięci wcześniej) — nie ma potrzeby jej wydłużać
- Page tokens nie wygasają → integracje działają nawet po wygaśnięciu konta użytkownika

**Problemy UX, które teraz rozumiem:**

| Problem | Przyczyna techniczna | Rozwiązanie UX |
|---------|---------------------|----------------|
| Użytkownik nagle traci dostęp bez ostrzeżenia | Brak timera w UI, idle timeout bez widocznego licznika | Pasywny toast „Sesja wygaśnie za 10 min" + opcja przedłużenia |
| „Sesja wygasła" pojawia się po nieudanym API calli | Walidacja tylko po stronie serwera, brak client-side check | Frontend powinien sprawdzać czas przed każdą akcją |
| Fallback na localStorage + URL param może wyciec | Implementacja bezpieczeństwa | To kwestia dev, nie UX — ale nie pokazuj session ID użytkownikowi nigdzie |

**Nowi użytkownicy (rola `viewer`):**
- Po zalogowaniu przez FB domyślnie dostają rolę `viewer` bez przypisanej placówki
- Efekt: widzą overlay „konto nie jest jeszcze zatwierdzone"
- Użytkownik nie rozumie dlaczego — wygląda jak błąd

→ Redesign: ekran „Czekamy na zatwierdzenie konta" z jasnym wyjaśnieniem i emailem do admina (zamiast ogólnego overlay).

---

## 2. MAPOWANIE PÓL — pełna mapa typów

### Co odkryłam

Istnieją **3 typy mapowań** (teraz to rozumiem w pełni):

#### Typ 1: Bezpośrednie mapowanie FB → Medidesk
Wartość z pola formularza FB trafia do pola Medidesk.  
Przykład: `phone_number` → `numer_telefonu_md`

#### Typ 2: Stałe wartości (`__const:wartość__`)
Zamiast pola z FB, wpisuje się z góry określony tekst.  
Przykład: `__const:Online Lead__` → pole `źródło` w Medidesk zawsze dostanie „Online Lead"  
To jest właśnie to tajemnicze `const:true` w interfejsie — tylko że wyświetlane źle.

#### Typ 3: Wirtualne pola (`__fb_*__`)
Metadane kampanii FB, nie z samego formularza:

| Kod | Co to jest | Po ludzku |
|-----|-----------|-----------|
| `__fb_form_name__` | Nazwa formularza FB | Nazwa reklamy |
| `__fb_lead_date__` | Data wypełnienia | Data leada |
| `__fb_ad_name__` | Nazwa reklamy | Nazwa reklamy |
| `__fb_campaign_name__` | Nazwa kampanii | Kampania |
| `__fb_platform__` | Urządzenie | Telefon / komputer |
| `__fb_is_organic__` | Organiczne / płatne | „tak" / „nie" |
| `__fb_lead_id__` | Unikalny ID leada | ID leada |

#### Scalanie pól
Kilka pól FB może trafiać do jednego pola Medidesk — wartości są łączone spacją.  
Przykład: `first_name` + `last_name` → `imie_i_nazwisko` = „Jan Kowalski"

### Implikacje dla UX

**Problem w obecnym UI:**
- `const:true` to błędna etykieta dla pola z wartością stałą
- Kod wirtualnego pola (`__fb_form_name__`) jest eksponowany użytkownikowi — kompletnie nieczytelny

**Jak to pokazać w redesignie:**

```
OBECNY WIDOK (krok 3 wizarda):
┌──────────────────┬──────────────────────────────────┐
│ FB               │ Medidesk                         │
├──────────────────┼──────────────────────────────────┤
│ phone_number     │ numer_telefonu_id_abc123          │
│ __const:true__   │ typ_kontaktu_id_xyz789            │
│ __fb_ad_name__   │ zrodlo_id_def456                  │
└──────────────────┴──────────────────────────────────┘

NOWY WIDOK (propozycja):
┌──────────────────────┬────────────────────┬─────────────────────┐
│ Pole z reklamy       │ Pole w Medidesk    │ Typ                 │
├──────────────────────┼────────────────────┼─────────────────────┤
│ Telefon              │ Numer telefonu     │ Z formularza        │
│ „Lead z Facebook"    │ Typ kontaktu       │ Wpisana stała       │
│ Nazwa reklamy        │ Źródło             │ Z kampanii FB       │
└──────────────────────┴────────────────────┴─────────────────────┘
```

Trzecia kolumna „Typ" eliminuje cały żargon — użytkownik rozumie co się dzieje.

---

## 3. WEBHOOK FLOW — pełna ścieżka leada

### Co odkryłam

Dokładna kolejność po tym jak Facebook wyśle zdarzenie:

```
1. Facebook wysyła POST na /webhook/facebook
2. Weryfikacja podpisu HMAC → jeśli fail: 403, lead znika bezpowrotnie
3. Szukaj aktywnej integracji po (page_id + form_id)
   └── Fallback: szukaj tylko po page_id
   └── Brak integracji → lead cicho zignorowany (tylko log)
4. Pobierz dane leada z Graph API (osobne żądanie HTTP)
   └── Jeśli fail → status "failed", koniec
5. Mapuj pola zgodnie z konfiguracją
   └── Jeśli żadne pole nie ma wartości → status "failed", koniec
6. Wyślij do Medidesk (URL-encoded POST, bez autoryzacji)
   └── Timeout: 15 sekund
7. Zapisz wynik w lead_events
```

### Implikacje dla UX

**Niewidoczne punkty awarii, które użytkownik powinien znać:**

| Gdzie może się posypać | Co widzi teraz | Co powinien widzieć |
|----------------------|----------------|---------------------|
| Brak aktywnej integracji | Nic (cichy log) | „Lead pominięty — integracja nieaktywna" |
| Błąd pobierania z FB API | ✗ w historii, bez opisu | „Nie udało się pobrać danych z Facebook — [Spróbuj ponownie]" |
| Timeout Medidesk (15s) | ✗ w historii, „Timeout" | „Formularz Medidesk nie odpowiedział — [Spróbuj ponownie]" |
| Medidesk 400 Bad Request | ✗ z surowym JSON błędu | „Medidesk odrzucił dane — sprawdź mapowanie pól" |

**Kluczowa implikacja dla historii leadów:**

W bazie są przechowywane `fb_raw_data` i `mapped_values` dla każdego leada.  
Oznacza to, że **retry jest technicznie możliwy** — dane są.  
Obecny UI nie oferuje retry w ogóle. To jest funkcja, którą warto dodać:

```
✗  Piotr Nowak  wczoraj 09:40  Błąd — Medidesk nie odpowiedział
                               [ Wyślij ponownie ]
```

---

## 4. MEDIDESK API — jak wygląda faktyczna integracja

### Co odkryłam

Medidesk przyjmuje dane przez **publiczny endpoint formularza** (bez autoryzacji):

```
POST https://app.medidesk.io/api/forms/{form_id}
Content-Type: application/x-www-form-urlencoded

siteDomain=medidesk.io&siteUrl=https://...&fieldsValues[idPola1]=wartość1&...
```

Brak tokenu, brak nagłówków autoryzacyjnych — to jest formularz webowy traktowany jak zwykłe zgłoszenie ze strony.

**Kody błędów Medidesk:**

| Kod | Znaczenie | Jak pokazać użytkownikowi |
|-----|-----------|--------------------------|
| 400 | Walidacja — brakujące pole lub zła wartość | „Medidesk odrzucił dane — prawdopodobnie brakuje wymaganego pola" |
| 502 | Medidesk niedostępny | „Formularz Medidesk chwilowo niedostępny — lead zostanie ponowiony" |
| 504 | Timeout | „Medidesk nie odpowiedział w czasie — [Spróbuj ponownie]" |
| Timeout (>15s) | Brak odpowiedzi | jw. |

### Implikacje dla UX

**Najważniejsze odkrycie:** błąd 400 (Bad Request) oznacza że Medidesk zwrócił JSON z listą błędów walidacji. Te błędy są logowane w `lead_events.error`. Teraz nie są pokazywane użytkownikowi w sensowny sposób.

**Co powinno się wydarzyć:**
- Błąd 400: wyciągnij czytelne pole z błędu (np. „Brakuje wartości dla pola: Telefon") i pokaż w historii leada
- Błąd 502/504: automatyczna kolejka retry (nie wymaga akcji użytkownika)
- Timeout: informacja + opcja ręcznego retry

**ID formularza Medidesk jest w URL-u, nie w ciele żądania.**  
To oznacza, że walidacja ID (krok 2 wizarda) może i powinna być zrobiona przez wywołanie `/api/forms/{id}` — jeśli odpowie, to ID jest poprawne. Aktualnie ta walidacja już istnieje, ale tylko po kliknięciu „Dalej". Wystarczy ją wywołać wcześniej (debounce 600ms).

---

## 5. FACEBOOK OAUTH — uprawnienia i token

### Co odkryłam

Aplikacja prosi o **6 uprawnień Facebook**:

| Uprawnienie | Po co |
|-------------|-------|
| `pages_show_list` | Lista stron użytkownika |
| `pages_read_engagement` | Odczyt danych strony |
| `pages_manage_ads` | Dostęp do kampanii (nazwa reklamy) |
| `pages_manage_metadata` | Metadane strony |
| `leads_retrieval` | Pobieranie leadów z Lead Ads |
| `business_management` | Strony przez Business Manager |

Token użytkownika: long-lived, ważny **60 dni**.  
Token strony: **nigdy nie wygasa**.  
Brak automatycznego odświeżania tokenu użytkownika — po 60 dniach użytkownik musi się ponownie zalogować.

Alert o wygasaniu: background job co 24h, sprawdza przez FB `debug_token` API, wysyła email przez Make.com jeśli zostało < 14 dni.

### Implikacje dla UX

**Aktualny problem:** użytkownik dostaje email (przez Make.com) kiedy token wygasa za < 14 dni, ale nie widzi nic w aplikacji.

**Propozycja:** alert w dashboardzie powinien pojawić się równolegle:

```
┌────────────────────────────────────────────────────────┐
│  🟡  Twój dostęp do Facebook wygasa za 8 dni           │
│      Połączenia przestaną działać 26 maja.             │
│                          [ Odnów dostęp ]  [ × ]       │
└────────────────────────────────────────────────────────┘
```

„Odnów dostęp" = ponowny login przez FB OAuth (wymiana tokenu).  
To jest możliwe technicznie — endpoint już istnieje.

**Krok 0 wizarda (logowanie) — ważny UX detail:**  
Dialog OAuth Facebooka prosi o sporo uprawnień — może to przestraszyć nieskupionego użytkownika.  
Przed kliknięciem „Zaloguj się przez Facebook" warto pokazać:
- Czego aplikacja **potrzebuje** (dostęp do leadów z reklam)
- Czego **nie robi** (nie publikuje, nie zarządza, nie widzi innych danych)

---

## 6. STANY BŁĘDÓW — pełna mapa

### Co odkryłam

Błędy dzielą się na **4 poziomy**:

#### Poziom 1 — Cicha awaria (użytkownik nie wie)
- Brak aktywnej integracji dla webhooka → lead zignorowany, tylko log
- Nieprawidłowy podpis webhooka → 403, żadnego śladu w UI

#### Poziom 2 — Widoczne w historii, ale nieczytelne
- Failed lead: `✗` z surowym JSON lub technicznym komunikatem
- Nie ma CTA, nie wiadomo co zrobić

#### Poziom 3 — Toast, ale za późno
- Błąd API po kliknięciu „Dalej" w wizardzie (np. złe ID Medidesk)
- Walidacja dopiero po akcji, nie w czasie wpisywania

#### Poziom 4 — Zewnętrzny email (nie w aplikacji)
- Token FB wygasa → email przez Make.com, brak alertu w UI

### Mapa błędów → komunikaty użytkownika

| Błąd techniczny | Obecny komunikat | Nowy komunikat |
|-----------------|------------------|----------------|
| 401 Unauthorized | Redirect do login | „Twoja sesja wygasła — zaloguj się ponownie" |
| 403 Forbidden | „Brak dostępu" | „Nie masz dostępu do tej integracji" |
| Unregistered role | Overlay (ogólny) | Dedykowany ekran z krokami co zrobić |
| Lead fetch fail | ✗ „failed" | „Nie udało się pobrać leada z Facebook — [Ponów]" |
| Medidesk 400 | ✗ JSON błędu | „Medidesk odrzucił dane — [szczegóły]" |
| Medidesk timeout | ✗ „Timeout" | „Medidesk nie odpowiedział — [Ponów]" |
| No mapped values | ✗ techniczny | „Żadne pole nie pasuje — sprawdź mapowanie" |
| Token expiry | Email (brak w UI) | Toast + banner w dashboardzie |

---

## 7. ADMIN vs UŻYTKOWNIK — realna różnica

### Co odkryłam

**4 role:** `admin`, `owner`, `viewer`, `user` (legacy = owner)

| Feature | Admin | Owner | Viewer |
|---------|-------|-------|--------|
| Widzi wszystkie integracje | ✅ | ❌ (tylko własna placówka) | ❌ |
| Tworzy integracje | ✅ | ✅ | ❌ |
| Edytuje mapowanie | ✅ | ✅ | ❌ |
| Widzi sekcję Placówki | ✅ | ❌ | ❌ |
| Zmienia hasło admina | ✅ | ❌ | ❌ |
| Zatwierdza nowych użytkowników | ✅ | ❌ | ❌ |
| Widzi historię leadów | ✅ | ✅ | ✅ |

**Nowi użytkownicy zawsze startują jako `viewer` bez przypisanej placówki.**  
Admin musi ich ręcznie promować. Brak mechanizmu self-service.

### Implikacje dla UX

**Największy problem:** viewer bez placówki widzi pusty dashboard z nakładką.  
Nie wie czy to błąd, czy ma coś zrobić.

**Propozycja dla ekranu „Konto niezatwierdzone":**

```
┌──────────────────────────────────────────────────┐
│                                                  │
│          Konto czeka na aktywację               │
│                                                  │
│  Twoje konto zostało zarejestrowane.            │
│  Administrator musi je zatwierdzić.             │
│                                                  │
│  Wyślij wiadomość do swojego admina:            │
│  admin@twojaplacowka.pl                         │
│                                                  │
│  (Ten adres można skonfigurować w ustawieniach) │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Dla admina — sekcja Zarządzanie użytkownikami:**  
Aktualnie zmieszana z listą placówek. Powinna być osobna zakładka z:
- Listą oczekujących na zatwierdzenie
- Opcją szybkiego przypisania do placówki + nadania roli

---

## DECYZJE PRODUKTOWE (potwierdzone)

| Temat | Decyzja |
|-------|---------|
| Retry leadów | Automatyczny przez 48h od błędu. Status w UI: „W kolejce do ponowienia" → po 48h „Nieudane". Brak ręcznego retry. |
| Email admina | Hardcoded: adminzoho@medidesk.com |
| System ról | MVP: jedna rola użytkownika = pełny dostęp do swojej placówki. Viewer usunięty. |
| Typy mapowania | Na start: tylko bezpośrednie FB → Medidesk. Const i wirtualne pola ukryte przed użytkownikiem. |

---

## PODSUMOWANIE — co zmienia ta analiza w redesignie

### Poprawki do dokumentu UX_REDESIGN.md (zaktualizowane o decyzje)

| # | Co zmieniam / doprecyzowuję | Status decyzji |
|---|---------------------------|----------------|
| 1 | Krok 3 wizarda: BEZ kolumny „Typ" — tylko FB→MD, typy ukryte | ✅ Zdecydowane |
| 2 | Historia leadów: status „W kolejce do ponowienia" / „Nieudane" — BEZ ręcznego retry | ✅ Zdecydowane |
| 3 | Dashboard: banner ostrzegający o wygasaniu tokenu FB (nie tylko email) | ✅ Zdecydowane |
| 4 | Ekran „Konto czeka na aktywację" z adresem adminzoho@medidesk.com | ✅ Zdecydowane |
| 5 | Błąd 400 od Medidesk: parsuj i pokaż czytelnie co konkretnie odrzucił | ✅ Zdecydowane |
| 6 | Przed loginiem FB: krótkie wyjaśnienie jakich uprawnień i dlaczego | ✅ Zdecydowane |
| 7 | Alert sesji: pasywny toast „Sesja wygaśnie za 10 min" zamiast nagłego wyrzucenia | ✅ Zdecydowane |
| 8 | Brak ekranu zarządzania rolami — jedna rola, admin zatwierdza ręcznie | ✅ Zdecydowane |

### Rzeczy, które NIE wymagają zmian w UX

- Mechanizm sesji 3h — to był świadomy wybór
- Page tokens bez wygasania — to zaleta, nie problem
- Brak autoryzacji do Medidesk API — tak działa ten endpoint, nie można zmienić
- Fuzzy matching AI — działa dobrze, wystarczy ukryć techniczne etykiety

### Otwarte pytania do Ciebie (przed implementacją)

1. **Retry leadów** — czy chcesz żeby użytkownik mógł ręcznie ponowić wysyłkę failed leada, czy to ma być automatyczne?
2. **Email admina** — adres do kontaktu dla niezatwierdzonych użytkowników — skąd ma pochodzić? Z konfiguracji systemu czy z profilu pierwszego admina?
3. **Viewer bez write access** — czy taka rola ma sens dla zwykłej recepcji? Czy wszyscy zalogowani użytkownicy placówki powinni móc tworzyć integracje?
4. **Kolumna „Typ" w mapowaniu** — czy użytkownik powinien móc sam wybierać typ (stała/FB/kampania) czy to tylko dla admina?
