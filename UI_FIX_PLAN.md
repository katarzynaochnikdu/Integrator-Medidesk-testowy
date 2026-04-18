# PLAN NAPRAW UI — FAZY

**Źródło bugów:** `UI_TEST_REPORT.md`
**Kolejność:** od największego user-visible impactu do kosmetyki
**Zasada:** jedna faza = jeden spójny PR, testowany w light + dark mode

---

## FAZA 1 — MODALE (impact: wszystkie modale w aplikacji)

**Cel:** modale zachowują się spójnie i profesjonalnie — dają się zamknąć klawiaturą, mają czytelne przyciski, działają w dark mode.

### Punkty do naprawy:
- **B1** — Escape zamyka modal (edycja mapowania + test połączenia + exit dialog)
- **B4** — Scrollbar w dark mode (modal edycji mapowania — biały track → dark)
- **U7** — "Anuluj" jako właściwy secondary button (border + hover state, nie sam tekst)

### Pliki do sprawdzenia:
- `app/templates/` — HTML modali (szukać `.modal`, `dialog`, `data-modal`)
- `app/static/` — JS obsługi modali (listener na `keydown` Escape)
- CSS z `::-webkit-scrollbar` (dla scrollbar stylingu)
- Komponent przycisku `.btn-secondary` / `.btn-ghost`

### Testy akceptacyjne:
- [ ] Escape zamyka modal edycji mapowania (light + dark)
- [ ] Escape zamyka modal "Test połączenia" (light + dark)
- [ ] Escape nie działa gdy kursor jest w polu input (nie traci danych)
- [ ] Scrollbar modalu w dark mode jest dark (track + thumb)
- [ ] "Anuluj" wygląda jak przycisk w obu motywach (border, hover)
- [ ] Kliknięcie poza modal (overlay) nadal zamyka — bez regresji

---

## FAZA 2 — POTWIERDZENIA I WALIDACJA (impact: destructive actions + setup)

**Cel:** akcje destrukcyjne mają potwierdzenie, błędy są widoczne długo enough.

### Punkty do naprawy:
- **B2** — "Wyślij ponownie" — dodać confirmation dialog (analogicznie do "Usuń z historii")
- **B6** — Inline walidacja pola "ID formularza Medidesk" — error pod polem, nie znikający toast

### Pliki do sprawdzenia:
- `app/templates/integration_detail.html` (lub gdzie jest tabela Historia leadów)
- Frontend handler `sendLeadAgain()` / `POST /leads/{id}/resend`
- Setup flow step 2: walidacja GUID/UUID format + sprawdzenie czy formularz istnieje w Medidesk API
- Istniejący komponent confirmation dialog (reużyć ten co "Usuń z historii")

### Testy akceptacyjne:
- [ ] Klik "Wyślij ponownie" → dialog "Czy na pewno wysłać lead X ponownie?"
- [ ] "Anuluj" → nic się nie dzieje, brak requestu
- [ ] "Potwierdź" → trigger retry + toast sukcesu
- [ ] Setup: wpisz losowy ciąg → inline error "Niepoprawny format ID" natychmiast
- [ ] Setup: poprawny format, ale nieistniejący ID → inline error "Nie znaleziono formularza w Medidesk"
- [ ] Error nie znika dopóki user nie zmieni value

---

## FAZA 3 — SEMANTYKA KOLORÓW METRYK (impact: pierwsze wrażenie)

**Cel:** kolory mają sens — zielony = dobrze, czerwony = źle, szary = neutralne.

### Punkty do naprawy:
- **U1** — BŁĘDY: 0 → szary/zielony (nie czerwony, 0 błędów to sukces)
- **U2** — SUKCES: 0% przy 0 leadów → szary "—" lub "brak danych" (nie pomarańczowy alarm)
- **U3** — AKTYWNE INTEGRACJE: 3 → zielony lub niebieski (nie różowo-czerwony)

### Pliki do sprawdzenia:
- `app/templates/dashboard.html` + `integration_detail.html` — karty metryk
- CSS klasy `.metric-value--error`, `.metric-value--warning`, `.metric-value--success`
- Ewentualnie helper w Jinja `{{ metric_color(błędy, 'errors') }}`

### Logika do zaimplementowania:
```
BŁĘDY:    0 → szary,  >0 → czerwony
SUKCES:   brak leadów → szary "—", 0-50% → czerwony, 51-90% → żółty, 91-100% → zielony
AKTYWNE:  zawsze zielony (to pozytywny stan)
LEADY:    zawsze niebieski/neutralny (info)
WYSŁANE:  zawsze zielony
```

### Testy akceptacyjne:
- [ ] Integracja bez leadów: SUKCES "—" szary, BŁĘDY "0" szary
- [ ] Integracja z leadami, 100%: SUKCES zielony 100%
- [ ] Integracja z błędami 50%: SUKCES żółty/pomarańczowy
- [ ] Dashboard: AKTYWNE INTEGRACJE zielony
- [ ] Nowa integracja po dodaniu → metryki od razu w poprawnych kolorach

---

## FAZA 4 — DASHBOARD PRZEGLĄD (impact: główny widok po zalogowaniu)

**Cel:** tabela leadów jest spójna i czytelna, filtry działają jak oczekujesz.

### Punkty do naprawy:
- **B3** — "pokaż wszystkie" w empty-state resetuje filtr do "Wszystkie"
- **B5** — Niespójne nazwy grup po Odśwież (jedna pełna nazwa, druga hash)
- **U6** — Usunąć kolumnę "INTEGRACJA" w tabeli (redundantna z nagłówkiem grupy)

### Pliki do sprawdzenia:
- `app/templates/dashboard.html` — tabela "Ostatnie leady"
- JS handler `refreshDashboard()` — logika renderowania nazwy grupy
- JS handler dla linku "pokaż wszystkie" (empty-state) — musi resetować filter state + URL param

### Testy akceptacyjne:
- [ ] Filtr "Problem" + brak wyników → "pokaż wszystkie" → filtr wraca do "Wszystkie", lista pełna
- [ ] Double-click Odśwież → wszystkie grupy pokazują tę samą konwencję nazw (nazwa integracji + fallback hash)
- [ ] Tabela ma kolumny: INTEGRACJA/LEAD ID, STATUS, POLA, KIEDY — bez zbędnej "INTEGRACJA" na końcu
- [ ] Responsive: na węższym viewport kolumny się nie zawijają głupio

---

## FAZA 5 — DROBIAZGI (impact: dopieszczenie)

**Cel:** usunąć literówki i edge case'y z mapowania pól.

### Punkty do naprawy:
- **D1** — "Zyczenie" → "Życzenie" (zmienić w źródle Medidesk API label OR frontend fallback-translation map)
- **D3** — Warning przy mapowaniu dwóch FB pól do tego samego Medidesk pola
- **U4** — Tooltip (title attribute lub popover) na obciętym tekście zgody
- **U5** — Przyjazne nazwy FB pól zamiast raw API (`phone_number` → "Numer telefonu", `first_name` → "Imię" itd.)
- **U8** — Swap prominenncji w exit-dialog — "Zostań" jako primary, "Przejdź do Dashboard" jako ghost (bezpieczniej)

### Pliki do sprawdzenia:
- Mapa tłumaczeń FB field names (stwórz jeśli nie ma): `app/utils/fb_fields.py` lub frontend lookup
- Tooltip CSS (sprawdzić czy jest komponent, jeśli nie — `title=""` jako fallback)
- JS walidator mapowania w modalu edycji
- `app/templates/setup.html` — exit dialog styles

### Testy akceptacyjne:
- [ ] "Życzenie" (z kropką nad Z) w modalu opcjonalnych pól
- [ ] Mapowanie first_name + last_name do "Imię-i-nazwisko" → ostrzeżenie "To pole Medidesk jest już zmapowane — ostatnia wartość nadpisze poprzednie"
- [ ] Hover na obciętej zgodzie → full text w tooltipie (native title lub custom)
- [ ] FB field "phone_number" wyświetla się jako "Numer telefonu (phone_number)" lub sam friendly name
- [ ] Exit dialog: "Zostań" primary (duży fiolet), "Przejdź do Dashboard" ghost (mały border)

---

## KOLEJNOŚĆ WDROŻEŃ

```
TYDZIEŃ 1:  FAZA 1 + FAZA 2 (wszystkie 🔴 bugi)    → gotowe do demo wewnętrznego
TYDZIEŃ 2:  FAZA 3 + FAZA 4 (kolory + dashboard)   → gotowe do demo zewnętrznego
TYDZIEŃ 3:  FAZA 5 (dopieszczenie)                 → production-ready
```

## CHECKPOINT PO KAŻDEJ FAZIE

- [ ] PR code review
- [ ] Test manualny w Chrome (light + dark mode)
- [ ] Test manualny w Firefox (bo scrollbar w FZ4 działa inaczej)
- [ ] Test na mobilce (viewport < 768px)
- [ ] Merge do main + deploy na Render
- [ ] Smoke test na produkcji (md-integrator-v1.onrender.com)
- [ ] Update statusu w `UI_TEST_REPORT.md` (przekreślić naprawione)

---

## POKRYCIE — MAPA BUG → FAZA

| Bug/Issue | Faza |
|-----------|------|
| B1 Escape nie zamyka modali | **1** |
| B2 Wyślij ponownie bez potwierdzenia | **2** |
| B3 pokaż wszystkie nie resetuje filtra | **4** |
| B4 Biały scrollbar w dark mode | **1** |
| B5 Niespójne nazwy grup po Odśwież | **4** |
| B6 Toast znika przy błędnym ID | **2** |
| U1 BŁĘDY 0 w czerwonym | **3** |
| U2 SUKCES 0% w pomarańczowym | **3** |
| U3 AKTYWNE w czerwonym | **3** |
| U4 Obcięta zgoda bez tooltipa | **5** |
| U5 Raw FB field names | **5** |
| U6 Zbędna kolumna INTEGRACJA | **4** |
| U7 Anuluj jako tekst nie button | **1** |
| U8 Zostań mniej prominent | **5** |
| D1 Zyczenie → Życzenie | **5** |
| D2 "2 wysyłek" niezrozumiałe | *(do dyskusji — tooltip/rename)* |
| D3 Duplikat Imie-i-nazwisko | **5** |

**Suma: 17 punktów rozłożonych na 5 faz.** Żaden bug nie ucieknie.
