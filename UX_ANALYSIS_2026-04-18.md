# Analiza UX/UI – Integracja Leadów do Medidesk

**Data:** 2026-04-18
**Aplikacja:** https://md-integrator-v1.onrender.com
**Perspektywa:** użytkownik operacyjny placówki medycznej (recepcjonistka / marketer), nie techniczny
**Tester:** Katarzyna Ochnik (zalogowana, 6 aktywnych integracji)

---

## ETAP 1 – Plan analizy

Zakres oceny:

- Pierwsze wrażenie (0–10 s): czy wiadomo, co to za system i co zrobić dalej
- Flow użytkownika: login → setup wizard (4 kroki) → dashboard → szczegóły integracji
- Architektura informacji: spójność nawigacji (landing vs wizard vs sidebar)
- Layout i ergonomia: scroll, sticky, wykorzystanie przestrzeni
- Kolorystyka i spójność wizualna: znaczenie kolorów, kontrast
- Komponenty UI: przyciski, formularze, listy, tabele
- Czytelność i obciążenie poznawcze: ile user musi myśleć
- Spójność: czy te same elementy zachowują się tak samo

---

## ETAP 2 – Obserwacje krok po kroku

### Login / landing po SSO

**Plus:** jasny tytuł, krótki opis, dwa wyraźne CTA, wskaźnik połączenia z Facebook.

**Minus:**
- Layout "kafelki 2 kolumny" sugeruje, że "Nowa integracja" i "Dashboard" są równorzędne, a dla nowego usera primary to "Nowa integracja".
- Stopka "API Docs" widoczna dla użytkownika operacyjnego – nie jego target.
- "Integracja Leadów do Medidesk v2.0" w stopce to metadata developerska.

### Setup wizard – krok 1 (Facebook)

3 sekcje pionowo: tożsamość → strona FB → formularz Lead Ads.

Problemy:
- Lista 18 formularzy bez paginacji wymusza długi scroll.
- Stepper na górze NIE jest sticky → przy scrollu user traci orientację.
- Placeholder "🔍 Filtruj po nazwie" miesza emoji z ikonografią SVG używaną gdzie indziej → niespójność.
- Tabela formularzy pokazuje kolumny LEADY / POLA / UTWORZONY – brak tooltipu wyjaśniającego, co oznacza "LEADY" (łącznie od zawsze? w tym miesiącu?).
- Badge "ACTIVE"/"ARCHIVED" po angielsku w polskim UI.
- 3 koncepty (tożsamość + strona FB + formularz) na jednym ekranie = wysokie obciążenie poznawcze przy pierwszej wizycie.

### Setup wizard – krok 2 (Medidesk)

Pusty ekran z jednym polem "ID formularza Medidesk" + przycisk "Pobierz pola".

Problemy krytyczne:
- **Brak instrukcji "skąd wziąć ID"** – najczęstsze miejsce porzucenia setupu dla non-tech usera.
- Brak linku do dokumentacji, brak screenshotu panelu Medidesk, brak walidacji formatu UUID.
- "Pobierz pola" – żargon. Lepiej: "Sprawdź formularz" lub "Pobierz pola formularza Medidesk".

### Dashboard – Przegląd

- 4 metryki w 4 różnych kolorach (niebieski / zielony / żółty / różowy) bez logiki semantycznej.
- Success rate 0% na żółto sugeruje "ostrzeżenie", choć to po prostu brak danych.
- Pusty stan: *"Brak danych — leady pojawią się po pierwszym webhookuw"* → **literówka** + słowo "webhook" (techniczny żargon).
- ID placówki "10245249520872946" wystawione w UI – nie potrzebne dziennemu userowi.

### Dashboard – Integracje

- Każda karta integracji powtarza metryki (0/0/0%) → wizualnie wygląda jakby system nie działał.
- Akcje "Dezaktywuj" i "Usuń" są wizualnie równorzędne z "Szczegóły". Destruktywne akcje powinny być wyciszone (ikona, menu kontekstowe).
- Możliwe duplikaty (dwa razy "Kurs MBM Black Friday v2") – brak walidacji unikalności przy tworzeniu integracji.
- Brak filtrowania po statusie, brak sortowania.

### Szczegóły integracji

- Sidebar pokazuje "E-book – Rewoluc" (ucięte) – sugeruje, że to pozycja menu, choć jest to kontekst bieżącej strony.
- Mapowanie pól pokazuje wartość "__const:true__" – czysty żargon dev, nieczytelny dla recepcjonistki.
- Brak breadcrumbs / kontekstu nawigacyjnego "Dashboard › Integracje › [nazwa]".
- Powtórzone statystyki (LEADY / WYSŁANE / BŁĘDY / SUCCESS) – duplikat z Dashboardu.

---

## ETAP 3 – Szczególny fokus

### Scroll vs sidebar

- Stepper i CTA "Dalej" w wizardzie **muszą być sticky**. Obecnie znikają przy scrollu listy 18 pozycji.
- Lista formularzy: zamiast tabeli 18 wierszy → "ostatnio użyte" na górze + sekcje kolapsowane ("Aktywne 18 / Zarchiwizowane 7").
- Widok szczegółów integracji: sidebar traci sens (ucięta nazwa) → zastąpić breadcrumbami.

### Setup experience

- Krok 1 ma 3 koncepty naraz → rozbić na progressive disclosure: najpierw strona FB, dopiero po wyborze pokazuje się lista formularzy.
- Krok 2 jest "naga" – wymaga przewodnika: "Gdzie znajdę ID formularza Medidesk?" + ikona ze screenshotem panelu Medidesk.
- Brak walidacji formatu UUID w kroku 2 → user dowie się o błędzie dopiero po kliknięciu "Pobierz pola".

### Kolor

- Brand violet OK, ale paleta metryk jest przypadkowa.
- Propozycja: wszystkie metryki neutralne (białe cyfry) + **semantyczny kolor tylko dla Success rate**:
  - ≥90 % → zielony
  - 50–90 % → żółty
  - <50 % → czerwony
  - brak danych → szary
- Czerwony jednocześnie dla "Błędów" i "Usuń" akceptowalny, ale Usuń powinno wymagać potwierdzenia.

### Hierarchia

- Na dashboardzie pusty stan nie kieruje użytkownika do akcji. Brak primary CTA "Wyślij testowy lead" / "Sprawdź konfigurację".
- W kroku 1 wizarda dwie sekcje (FB strona + Formularz) wyglądają identycznie – brak akcentu na bieżącym kroku.

---

## ETAP 4 – Podsumowanie

### Top 5 problemów UX

1. **Krok 2 bez guidance** – brak instrukcji "skąd wziąć ID Medidesk" → najczęstsze miejsce drop-offu w setupie.
2. **Stepper i przyciski nie są sticky** → użytkownik gubi się przy scrollu listy formularzy.
3. **Pusty stan dashboardu** – techniczny żargon ("webhook") + literówka ("webhookuw").
4. **Mapowanie pól** pokazuje techniczny zapis "__const:true__" – nieczytelne dla non-dev usera.
5. **Niespójna paleta metryk** – żółty 0 % sugeruje błąd, choć to brak danych.

### Top 5 quick wins

1. Literówka "webhookuw" → "webhooku" (5 min).
2. Link/tooltip "Gdzie znajdę ID formularza Medidesk?" w kroku 2.
3. Sticky stepper + sticky stopka "Wstecz / Dalej" w wizardzie.
4. Ujednolicić paletę: metryki neutralne, kolor tylko dla statusów.
5. Ukryć "API Docs" i ID placówki z UI dla zwykłego usera (przenieść do Ustawień).

### Ocena ogólna: 6/10

Solidna, działająca aplikacja z czytelnym flow i dobrym brandingiem. Traci punkty na drobnych, ale uciążliwych potknięciach (żargon, literówka, niespójność kolorów, brak guidance w kroku 2). To różnica między "działa" a "łatwo i miło".

### Skalowalność

Średnia. Przy większej liczbie danych:

- Lista formularzy bez paginacji – 18 już wymaga scrolla; przy 100+ nieużywalna.
- Lista integracji bez filtrowania po statusie utonie. Potrzebny widok "tylko z błędami".
- Tabela "Ostatnie leady" wymaga filtrów po dacie, statusie, integracji.
- Sidebar dynamicznie wstawiający nazwę integracji nie skaluje się → breadcrumbs.
- Brak alertów o integracjach, które przestały działać – user nie wie, że jest problem, póki nie zajrzy ręcznie.

---

## Tryb bezlitosny

**Użytkownik pierwszy raz, bez szkolenia:** dociera do kroku 2, widzi "ID formularza Medidesk", nie wie skąd to wziąć, zamyka aplikację. Szacowany drop-off: ~70 %.

**Użytkownik zmęczony:** scrolluje listę 18 formularzy, gubi stepper, zapomina po co tu wszedł, scrolluje z powrotem na górę.

**Użytkownik z 50 integracjami za rok:** lista nieczytelna, brak filtrowania "pokaż tylko z błędami", brak alertów gdy integracja przestaje działać → przegapi problem u klienta.
