# RAPORT KOŃCOWY — TESTY UI Medidesk Integrator

**URL:** https://md-integrator-v1.onrender.com  
**Data testu:** 2026-04-18  
**Tryby:** Light Mode + Dark Mode  
**Przeglądarka:** Chrome (profil Placowka)  
**Styl testowania:** first-time user / zmęczony user / szybki chaotyczny clicker

---

## 🔴 BUGI (twarde błędy, do naprawy przed pokazaniem)

| # | Opis | Gdzie | Priorytet |
|---|------|-------|-----------|
| B1 | **Escape nie zamyka żadnego modalu** — ani edycji mapowania, ani testu połączenia. Jedyna opcja to kliknięcie X lub "Anuluj" | Mapowanie modal, Test modal | **Wysoki** |
| B2 | **"Wyślij ponownie" bez potwierdzenia** — klika i od razu retryuje. Brak confirmation dialog (w przeciwieństwie do "Usuń z historii" które ma). Niespójne zachowanie | Historia leadów | **Wysoki** |
| B3 | **"pokaż wszystkie" w empty-state nie resetuje filtra** — po kliknięciu URL się nie zmienia i filtr "Problem" zostaje aktywny, lista nadal pusta | Integracje, empty state | **Średni** |
| B4 | **Biały scrollbar w ciemnym modalu edycji mapowania** — natywny scrollbar przeglądarki nie jest wystylowany pod dark mode, biały track na ciemnym tle | Dark mode, modal mapowania | **Średni** |
| B5 | **Po double-click "Odśwież" — niespójne nazwy grup** — jedna grupa pokazuje pełną nazwę integracji, druga hash ID | Dashboard Przegląd | **Niski** |
| B6 | **Toast błędu (błędny ID Medidesk) znika natychmiast** — brak inline walidacji przy polu | Setup krok 2 | **Niski** |

---

## 🟡 PROBLEMY UX (nie blokują, ale gryzą)

| # | Opis | Gdzie |
|---|------|-------|
| U1 | **BŁĘDY: 0 wyświetlone w czerwonym** — 0 błędów to sukces, nie alarm. Powinien być szary lub zielony | Metryki integracji |
| U2 | **SUKCES: 0% w pomarańczowym** — nowa integracja bez leadów wyświetla 0% jakby coś było nie tak | Metryki integracji |
| U3 | **AKTYWNE INTEGRACJE: 3 w różowo-czerwonym** — semantycznie mylące, aktywny = dobry, powinien być zielony/niebieski | Dashboard Przegląd |
| U4 | **Tekst zgód obcięty elipsą bez tooltipa** — użytkownik nie może zobaczyć pełnej treści zgody w widoku mapowania | Tabela mapowania, modal |
| U5 | **Raw FB API nazwy pól** (phone_number, first_name, last_name, email) — nie-technicznym użytkownikom nic nie mówią | Wszędzie — tabela mapowania |
| U6 | **Kolumna "INTEGRACJA" w tabeli Przegląd** — powtarza hash ID który jest już w nazwie grupy, kolumna zbędna | Dashboard Przegląd |
| U7 | **"Anuluj" w modalach jest prawie niewidoczny jako przycisk** — szczególnie w dark mode, wygląda jak tekst a nie button | Wszystkie modale |
| U8 | **"Zostań" w dialogu wyjścia jest mniej prominent niż "Przejdź do Dashboard"** — bezpieczna akcja powinna być bardziej widoczna | Setup flow, exit dialog |

---

## 🔵 DROBIAZGI (kosmetyka / literówki)

| # | Opis | Gdzie |
|---|------|-------|
| D1 | **"Zyczenie" zamiast "Życzenie"** — brak diakrytyku, pochodzi z API Medidesk | Modal mapowania — opcjonalne pola |
| D2 | **"2 wysyłek"** — badge licznika wysyłek może być niezrozumiały dla nietech. użytkowników | Tabela Przegląd |
| D3 | **first_name + last_name oba mapowane do "Imię-i-nazwisko"** — brak ostrzeżenia o duplikacji pola docelowego | Modal edycji mapowania |

---

## ✅ CO DZIAŁA ŚWIETNIE

- **Dark mode ogólnie** — świetne kontrasty, spójna paleta, brak "znikających" elementów
- **Stepper w setup flow** — ✓ na ukończonych krokach, aktywny krok wyróżniony, czytelna progresja
- **"Opcjonalne pola Medidesk"** sekcja z amber/złotym tłem — piękna, intuicyjna
- **Exit dialog** ("Na pewno chcesz wyjść?") — doskonały: żółty ⚠️ ikonka, jasny tekst, blur backdrop
- **Filtry na liście integracji** — kolorowe dotki statusów, czytelna liczba
- **Toast notyfikacje** — czytelne, poprawnie kolorowane (zielony sukces, czerwony błąd)
- **Formularz FB — lista formularzy z filtrem i sortowaniem** — działa perfekcyjnie
- **Mapowanie pól: zielone Medidesk + niebieskie FB** — doskonała semantyka kolorów
- **Confirmation dialogi dla "Usuń z historii" i "Usuń integrację"** — obecne i poprawne
- **Responsywność** — płynne ładowanie, brak zamrożeń przy normalnym użytkowaniu

---

## VERDICT

> **Gotowe do pokazania? ⚠️ PRAWIE — NIE W TYM TYGODNIU**

Aplikacja wygląda **profesjonalnie i dojrzale**, dark mode jest naprawdę dobry. Ale 2 bugi wysokiego priorytetu (Escape + "Wyślij ponownie" bez potwierdzenia) i kilka dezorientujących kolorów semantycznych (błędy w czerwonym przy 0, aktywne integracje w różowym) mogą zepsuć pierwsze wrażenie technicznego użytkownika.

**Po naprawieniu B1, B2, U1–U3 → pełne TAK do pokazania.** Reszta to lista na sprint.
