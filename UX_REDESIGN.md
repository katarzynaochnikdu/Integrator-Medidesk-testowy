# Integracja Leadów do Medidesk — Przebudowa UX/UI
> Dokument projektowy · Wersja 1.0 · Kwiecień 2026

---

## ETAP 1 — FUNDAMENTY UX

### 1.1 Główne zadanie użytkownika

> „Chcę, żeby leady z reklamy Facebook trafiały do Medidesk — i żeby to działało samo."

Użytkownik chce to zrobić **raz, w 5 minut**, a potem **już tego nie dotykać**.  
Ewentualnie: wrócić kiedy „coś przestało działać" i zrozumieć dlaczego.

Dwa zadania, dwa tryby — nie ma sensu mieszać ich w jednym ekranie.

---

### 1.2 Największe ryzyka UX

| # | Gdzie | Problem | Skutek |
|---|-------|---------|--------|
| 1 | Krok 2 setupu | Brak instrukcji skąd wziąć ID formularza Medidesk | ~70% porzuceń |
| 2 | Lista kroków | Stepper znika przy scrollowaniu listy formularzy | Użytkownik nie wie gdzie jest |
| 3 | Mapowanie pól | Etykiety techniczne (`const:true`, UUID) | Panika, błędy, telefon do supportu |
| 4 | Dashboard | KPI bez kontekstu (0% success wyświetla się na żółto) | Fałszywy alarm |
| 5 | Pusty stan | Brak akcji po komunikacie | Użytkownik nie wie co robić dalej |
| 6 | Błędy walidacji | Dopiero po kliknięciu „Dalej" | Za późno — frustracja |

---

### 1.3 Model mentalny użytkownika

Użytkownik **nie myśli** o webhookach, API, UUID ani mapowaniu pól.  
Użytkownik myśli:

```
Reklama na FB → formularz → pacjent trafia do Medidesk
```

Dlatego cały interfejs powinien używać **jego języka**:

| Żargon techniczny | Język użytkownika |
|---|---|
| Webhook | — (ukryty) |
| UUID / ID formularza | Numer formularza w Medidesk |
| const:true | Wypełniane automatycznie |
| Field mapping | Dopasowanie pól |
| Integration | Połączenie |
| Active / Archived | Działa / Wyłączone |
| API Docs | — (usuń) |
| Facility ID | — (ukryj dla nie-adminów) |

---

## ETAP 2 — ARCHITEKTURA UI

### 2.1 Dwa tryby — dwa widoki

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   TRYB SETUP (wizard)          TRYB OPERACYJNY      │
│   Pierwsze uruchomienie        Dashboard po setupie │
│   lub dodanie integracji       Monitoring i edycja  │
│                                                     │
│   Krok po kroku                Lista połączeń       │
│   Jeden ekran = jeden cel      Status + alerty      │
│   Brak sidebar                 Breadcrumbs          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Sidebar usuń.** Sidebar to nawigacja dla power userów. Ten użytkownik nie potrzebuje bocznego menu z 5 opcjami — potrzebuje jednej drogi do przodu.

---

### 2.2 Struktura nawigacji

```
[Logowanie FB]
      ↓
[Dashboard — lista połączeń]
      ↓              ↓
[+ Nowe połączenie]  [Szczegóły połączenia]
      ↓                      ↓
[Wizard 4 kroki]      [Edycja / Historia / Status]
```

Nawigacja górna (topbar), nie boczna. Tylko 2 elementy:
- Logo / nazwa
- Avatar użytkownika + wyloguj

---

### 2.3 SETUP WIZARD — nowy flow

**Zasada: zero scrolla, jeden cel na ekran.**

---

#### KROK 0 — Logowanie

```
┌──────────────────────────────────────────────────┐
│                                                  │
│              🏥 Integracja Leadów do Medidesk              │
│                                                  │
│   Połącz reklamy Facebook z formularzami         │
│   Medidesk — automatycznie.                      │
│                                                  │
│         [ Zaloguj się przez Facebook ]           │
│                                                  │
│   Potrzebujesz dostępu do swojej strony FB.      │
│                                                  │
└──────────────────────────────────────────────────┘
```

- Jedno CTA
- Krótkie wyjaśnienie po co jest login
- Brak marketingowego bełkotu

---

#### KROK 1 — Wybierz stronę Facebook i reklamę

```
┌──────────────────────────────────────────────────┐
│  ← Anuluj                    Krok 1 z 4 ●○○○   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Która reklama zbiera leady?                     │
│                                                  │
│  Strona Facebook                                 │
│  ┌────────────────────────────────────────────┐  │
│  │ ▼  Centrum Medyczne Słoneczna              │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Formularz reklamowy                             │
│  ┌────────────────────────────────────────────┐  │
│  │ ○  Formularz — Ortopeda Maj 2025           │  │
│  │ ○  Formularz — Dermatologia wiosna         │  │
│  │ ●  Formularz — Stomatologia promocja       │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│                        [ Dalej → ]               │
└──────────────────────────────────────────────────┘
```

**Zmiany vs obecnie:**
- Dropdown zamiast scrollowalnej listy stron FB (jeśli > 3 strony)
- Lista formularzy: radio buttons, max 6 widocznych + „Pokaż więcej"
- Stepper zawsze widoczny (sticky top bar)
- CTA jedno, wyraźne, dopiero po wybraniu aktywne (disabled state)

---

#### KROK 2 — Podaj numer formularza Medidesk

```
┌──────────────────────────────────────────────────┐
│  ← Wstecz                    Krok 2 z 4 ●●○○   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Który formularz Medidesk ma odbierać leady?     │
│                                                  │
│  Numer formularza                                │
│  ┌────────────────────────────────────────────┐  │
│  │  np. ABC-12345                             │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ℹ️  Gdzie znajdziesz numer?                     │
│  ┌────────────────────────────────────────────┐  │
│  │  1. Otwórz Medidesk                        │  │
│  │  2. Idź do: Formularze → Lista             │  │
│  │  3. Kliknij formularz → skopiuj numer      │  │
│  │     z paska adresu lub nagłówka            │  │
│  │                                            │  │
│  │  📸 [Pokaż zrzut ekranu]                   │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ✓ Znaleziono: „Formularz kontaktowy — Ortopeda" │
│                                                  │
│                        [ Dalej → ]               │
└──────────────────────────────────────────────────┘
```

**Zmiany vs obecnie:**
- Inline guidance — zawsze widoczna, nie schowana za tooltipem
- Walidacja w czasie rzeczywistym (po wklejeniu ID, bez klikania)
- Po znalezieniu formularza: czytelne potwierdzenie nazwy (nie UUID)
- CTA aktywne dopiero po udanej walidacji
- Zrzut ekranu jako opcjonalna pomoc (modal lub accordion)

---

#### KROK 3 — Dopasuj pola

```
┌──────────────────────────────────────────────────┐
│  ← Wstecz                    Krok 3 z 4 ●●●○   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Sprawdź, czy pola są dopasowane poprawnie       │
│                                                  │
│  Wygenerowaliśmy dopasowanie automatycznie.      │
│  Możesz je zmienić jeśli coś się nie zgadza.    │
│                                                  │
│  ┌──────────────────┬──────────────────────────┐ │
│  │ Pole z reklamy   │ Pole w Medidesk          │ │
│  ├──────────────────┼──────────────────────────┤ │
│  │ Imię i nazwisko  │ ▼ Imię i nazwisko    ✓  │ │
│  │ Telefon          │ ▼ Numer telefonu     ✓  │ │
│  │ Email            │ ▼ Adres e-mail       ✓  │ │
│  │ Miasto           │ ▼ Miasto             ✓  │ │
│  └──────────────────┴──────────────────────────┘ │
│                                                  │
│  ℹ️  „Wypełniane automatycznie" — to pola, które │
│  Medidesk uzupełni sam (nie musisz ich zmieniać) │
│                                                  │
│                        [ Dalej → ]               │
└──────────────────────────────────────────────────┘
```

**Zmiany vs obecnie:**
- Usuń `const:true` — zastąp „Wypełniane automatycznie"
- Usuń UUID z widoku — pokaż tylko nazwy pól
- Status ✓ / ⚠ przy każdym dopasowaniu (nie tylko globalny)
- Tylko niedopasowane pola oznaczone ⚠ wymagają uwagi
- Krótkie wyjaśnienie czym są pola automatyczne

---

#### KROK 4 — Potwierdzenie

```
┌──────────────────────────────────────────────────┐
│  ← Wstecz                    Krok 4 z 4 ●●●●   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Wszystko gotowe — sprawdź szczegóły             │
│                                                  │
│  📄 Formularz reklamy:                           │
│     Stomatologia promocja (Facebook)             │
│                                                  │
│  🏥 Formularz Medidesk:                          │
│     Formularz kontaktowy — Stomatologia          │
│                                                  │
│  🔗 Pola:  4 dopasowane automatycznie            │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │  ✓  Uruchom połączenie                     │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Możesz je wyłączyć lub usunąć w każdej chwili  │
│  z poziomu dashboardu.                           │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

#### STAN PO KLIKNIĘCIU „Uruchom połączenie"

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  ⏳ Sprawdzamy połączenie z Facebook…            │
│  ⏳ Rejestrujemy odbiór leadów…                  │
│  ✓  Połączenie aktywne!                          │
│                                                  │
│           [ Przejdź do dashboardu ]              │
│                                                  │
└──────────────────────────────────────────────────┘
```

- Sekwencyjne komunikaty (nie spinner bez informacji)
- Czas oczekiwania < 3 sekundy → auto-redirect do dashboardu
- Czas > 3 sekundy → zostaje komunikat + CTA

---

### 2.4 DASHBOARD — tryb operacyjny

#### Widok główny — lista połączeń

```
┌──────────────────────────────────────────────────────────────────┐
│  🏥 Integracja Leadów do Medidesk          [Kasia K.]  [+ Nowe połączenie] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Twoje połączenia (3)                                            │
│                                                                  │
│  [ Wszystkie ▼ ]  [ 🔍 Szukaj ]                                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  🟢 Stomatologia — Promocja wiosenna                     │    │
│  │     Ostatni lead: dziś, 14:32 · 47 leadów łącznie       │    │
│  │                              [ Szczegóły ]  [ ⋮ ]       │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │  🟢 Ortopedia — Marzec 2025                              │    │
│  │     Ostatni lead: wczoraj · 12 leadów łącznie           │    │
│  │                              [ Szczegóły ]  [ ⋮ ]       │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │  🔴 Dermatologia — Lato                                  │    │
│  │     Problem z połączeniem · Ostatni lead: 5 dni temu    │    │
│  │     ⚠ Sprawdź połączenie                                 │    │
│  │                              [ Sprawdź ]  [ ⋮ ]         │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Zmiany vs obecnie:**
- Usunięto KPI cards z góry (bezsensowne sumy w kontekście monitoringu)
- Kolor = status (🟢/🔴/🟡) — semantyczny
- CTA w wierszu z problemem zmienia się na „Sprawdź" (nie „Szczegóły")
- Filtr dropdown: Wszystkie / Działające / Z problemem / Wyłączone
- Menu ⋮: Wyłącz / Usuń połączenie (ukrywa destrukcyjne akcje)

---

#### Pusty stan (zero połączeń)

```
┌──────────────────────────────────────────────────┐
│                                                  │
│             Brak połączeń                        │
│                                                  │
│   Połącz formularz reklamowy Facebook            │
│   z formularzem Medidesk — leady będą            │
│   trafiać automatycznie.                         │
│                                                  │
│         [ + Utwórz pierwsze połączenie ]         │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

#### Alert — integracja przestała działać

Toast (auto-znikający po 8 sek., z opcją „Sprawdź teraz"):

```
┌────────────────────────────────────────────────────┐
│  🔴  Połączenie „Dermatologia — Lato" ma problem   │
│       Leady nie trafiają do Medidesk               │
│                          [ Sprawdź ]  [ × ]        │
└────────────────────────────────────────────────────┘
```

---

### 2.5 SZCZEGÓŁY POŁĄCZENIA

```
┌──────────────────────────────────────────────────────────────────┐
│  🏥 Integracja Leadów do Medidesk     Moje połączenia > Stomatologia       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🟢 Stomatologia — Promocja wiosenna                             │
│     Aktywne od: 10 marca 2025                                    │
│                                                                  │
│  ──────────────────────────────────────────────────              │
│  STATYSTYKI                                                      │
│  47 leadów odebranych · 45 wysłanych · 2 błędy                  │
│                                                                  │
│  ──────────────────────────────────────────────────              │
│  DOPASOWANIE PÓL                          [ Edytuj ]             │
│                                                                  │
│  Imię i nazwisko    →   Imię i nazwisko                          │
│  Telefon            →   Numer telefonu                           │
│  Email              →   Adres e-mail                             │
│  Miasto             →   Miasto                                   │
│  —                  →   Źródło (wypełniane automatycznie)        │
│                                                                  │
│  ──────────────────────────────────────────────────              │
│  OSTATNIE LEADY                                                  │
│                                                                  │
│  ✓  Jan Kowalski        dziś 14:32      Wysłany                  │
│  ✓  Anna Wiśniewska     dziś 11:15      Wysłany                  │
│  ✗  Piotr Nowak         wczoraj 9:40   Błąd — spróbuj ponownie  │
│                                                                  │
│                                      [ Wyłącz połączenie ]       │
└──────────────────────────────────────────────────────────────────┘
```

**Zmiany vs obecnie:**
- Breadcrumbs zamiast sidebara
- Statystyki: 3 liczby w jednej linii (nie 4 karty z kolorami)
- Mapowanie pól: nazwy użytkownika (nie UUID/const:true)
- „Źródło (wypełniane automatycznie)" zamiast `const:true`
- Tabela leadów: tylko niezbędne kolumny, błąd ma CTA „spróbuj ponownie"
- Czerwony przycisk „Wyłącz" na dole (nie w nagłówku)

---

## ETAP 3 — SYSTEM WIZUALNY

### 3.1 Light Mode First

**Palette:**

| Element | Kolor | HEX |
|---------|-------|-----|
| Tło | Biały | `#FFFFFF` |
| Tło sekcji | Jasnoszary | `#F8F9FA` |
| Ramki | Szary | `#E5E7EB` |
| Tekst główny | Prawie czarny | `#111827` |
| Tekst pomocniczy | Szary | `#6B7280` |
| Primary CTA | Granatowy (marka) | `#1D4ED8` |
| CTA hover | Ciemniejszy | `#1E40AF` |

**Typografia:**
- Font: Inter lub systemowy (San Francisco / Segoe UI)
- Nagłówki: 20–24px, semibold
- Treść: 15–16px, regular
- Pomoc/etykiety: 13px, medium, szary

---

### 3.2 Kolor = Semantyka

| Stan | Kolor | Zastosowanie |
|------|-------|-------------|
| 🟢 Działa | `#16A34A` zielony | Aktywne połączenie, udany lead |
| 🔴 Błąd | `#DC2626` czerwony | Problem z połączeniem, nieudany lead |
| 🟡 Uwaga | `#D97706` żółty | Token wygasa, brak danych > 48h |
| ⚪ Brak danych | `#9CA3AF` szary | Nowe połączenie bez historii |
| 🔵 W trakcie | `#2563EB` niebieski | Ładowanie, weryfikacja |

**Usuń:** losowe kolory na kartach KPI (niebieski/zielony/żółty/czerwony bez znaczenia).

---

### 3.3 Hierarchia CTA

Na każdym ekranie:
- **1 primary button** (pełny kolor, wyraźny)
- **Maks. 1 secondary button** (outlined lub ghost)
- **Destrukcyjne akcje** (Usuń, Wyłącz): schowane w menu ⋮ lub na dole ekranu, nigdy obok primary CTA

---

## ETAP 4 — INTERAKCJE

### 4.1 Loading i weryfikacja — bez mignięć

**Zamiast:** spinner bez opisu  
**Zamiast:** błąd po 3 sekundach ciszy

**Zamiast tego — sekwencyjne komunikaty:**

```
⏳ Sprawdzamy połączenie z Facebook…      (0–1s)
⏳ Pobieramy formularze reklamowe…        (1–2s)
✓  Gotowe — znaleziono 3 formularze       (2s+)
```

**Reguły:**
- Po 3s bez odpowiedzi: komunikat „To trwa dłużej niż zwykle…"
- Po 10s: „Coś poszło nie tak — [Spróbuj ponownie]"
- Nigdy błąd bez CTA

---

### 4.2 Walidacja w czasie rzeczywistym

| Pole | Kiedy waliduj | Jak |
|------|--------------|-----|
| ID formularza Medidesk | Po wklejeniu (debounce 600ms) | Zielona ramka + nazwa formularza |
| Wybór strony FB | Po wybraniu | Lista formularzy ładuje się od razu |
| Mapowanie pól | Na bieżąco | ✓ zielony lub ⚠ żółty przy każdym wierszu |

---

### 4.3 Toast notifications

Zasady:
- Sukces: zielony toast, 4 sekundy, auto-znika
- Błąd: czerwony toast, zostaje do kliknięcia × lub podjęcia akcji
- Ostrzeżenie: żółty toast, 8 sekund

Przykłady komunikatów:
- ✓ „Połączenie uruchomione — leady będą trafiać do Medidesk"
- ✗ „Nie udało się połączyć — sprawdź numer formularza Medidesk"
- ⚠ „Dostęp do Facebooka wygasa za 3 dni — [Odśwież dostęp]"

---

### 4.4 Feedback — użytkownik zawsze wie

| Sytuacja | Co widzi użytkownik |
|----------|---------------------|
| Lead przyszedł | Nowa pozycja w historii + licznik rośnie |
| Lead nieudany | ✗ w historii + „Błąd — spróbuj ponownie" |
| Połączenie nieaktywne | 🔴 na liście + alert toast |
| Token FB wygasa | ⚠ żółty alert na dashboardzie |
| Setup ukończony | Ekran potwierdzenia + auto-redirect |

---

## ETAP 5 — LISTA USUNIĘĆ

### Usuń z interfejsu:

| Element | Powód |
|---------|-------|
| `const:true` | Żargon developerski |
| UUID w widoku | Niezrozumiałe, niepotrzebne |
| „webhook" w komunikatach | Jargon techniczny |
| „ID placówki" (dla nie-adminów) | Nie dotyczy ich roli |
| Link „API Docs" | Nie dla tej grupy użytkowników |
| 4 kolorowe karty KPI | Brak wartości semantycznej |
| Badge „ACTIVE" / „ARCHIVED" po ang. | Niespójne z polskim UI |
| Typo „webhookuw" | Błąd językowy |
| Sidebar z rozwijanymi integracjami | Zbyt złożony dla tego use case'u |

---

## ETAP 6 — OUTPUT / PODSUMOWANIE

### 6.1 Nowy model UI — ekrany

```
1. Login (FB OAuth)
2. Dashboard — lista połączeń
   └─ Pusty stan z CTA
   └─ Lista z filtrami i statusami
3. Wizard (4 kroki, zero scrolla)
   └─ Krok 1: Wybór strony + formularza FB
   └─ Krok 2: ID Medidesk + inline guidance
   └─ Krok 3: Mapowanie pól (user language)
   └─ Krok 4: Potwierdzenie + uruchomienie
4. Szczegóły połączenia
   └─ Breadcrumbs
   └─ Statystyki (1 linia)
   └─ Mapowanie pól (edytowalne)
   └─ Historia leadów
5. (Admin) Zarządzanie placówkami — oddzielny panel
```

---

### 6.2 Nowy flow użytkownika

```
Login FB (20s)
     ↓
Dashboard — widzi swoje połączenia
     ↓
Klik "+ Nowe połączenie"
     ↓
Wizard krok 1: Wybiera stronę + formularz FB (30s)
     ↓
Wizard krok 2: Wkleja ID Medidesk, widzi potwierdzenie nazwy (45s)
     ↓
Wizard krok 3: Sprawdza dopasowanie pól, korekta jeśli trzeba (60s)
     ↓
Wizard krok 4: Potwierdza, klika "Uruchom"
     ↓
Ekran sukcesu → auto-redirect do dashboardu
     ↓
🟢 Nowe połączenie widoczne na liście

Łącznie: ~3–4 minuty (vs ~10–15 min obecnie)
```

---

### 6.3 Kluczowe zmiany vs obecny system

| Obszar | Teraz | Po redesignie |
|--------|-------|---------------|
| Nawigacja | Sidebar | Topbar + breadcrumbs |
| Setup | Nielinearny, z scrollem | Wizard 4 kroki, zero scrolla |
| Guidance | Brak (tooltip tylko) | Inline, zawsze widoczna |
| Język | Techniczny (UUID, const, webhook) | Użytkownika (nazwy, opisy) |
| Kolory | Dekoracyjne | Semantyczne (status = kolor) |
| Walidacja | Po kliknięciu „Dalej" | Real-time (debounce) |
| Loading | Spinner bez info | Sekwencyjne komunikaty |
| Pusty stan | Komunikat bez akcji | Komunikat + CTA |
| Błąd | Komunikat techniczny | Komunikat + „Spróbuj ponownie" |
| KPI | 4 karty z losowymi kolorami | 3 liczby w 1 linii |
| Admin | Zmieszany z UI użytkownika | Osobny panel |

---

### 6.4 Największy impact

**UX:**
- Inline guidance przy ID Medidesk eliminuje ~70% porzuceń w kroku 2
- Wizard bez scrolla eliminuje dezorientację nawigacyjną
- Semantyczne kolory eliminują fałszywe alarmy i chaos wizualny

**Biznes:**
- Drop-off setup: szacowany spadek z ~60% → ~15%
- Czas setupu: z ~10–15 min → ~3–4 min
- Liczba zgłoszeń do supportu: spadek o szacowane 50–70% (guidance + jasne błędy)
- Time-to-value: pierwszy działający lead w <5 min od logowania

---

## APPENDIX — Priorytetyzacja wdrożenia

### Quick wins (< 1 dzień):
1. Zmień `const:true` → „Wypełniane automatycznie"
2. Usuń link „API Docs"
3. Ukryj UUID z widoku mapowania
4. Napraw typo „webhookuw"
5. Zmień badge ACTIVE/ARCHIVED na „Działa" / „Wyłączone"

### Medium (1–3 dni):
6. Inline guidance dla pola ID Medidesk
7. Sticky stepper (CSS fix)
8. Semantyczne kolory statusów
9. Pusty stan z CTA
10. Real-time walidacja ID formularza

### Duże zmiany (1–2 tygodnie):
11. Zamiana sidebara na topbar + breadcrumbs
12. Redesign wizard — zero scrolla
13. Toast notification system
14. Sekwencyjne komunikaty ładowania
15. Light mode (aktualnie dark theme)
