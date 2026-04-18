# 📋 Work Order Template

> Szablon zlecenia przekazywanego workerowi. Skopiuj i wypełnij.

---

## Work Order #[NUMER]

**Data**: [DATA]  
**Worker**: [NAZWA WORKERA]  
**Priorytet**: [🔴 Krytyczny / 🟡 Normalny / 🟢 Niski]  
**Snapshot**: [TAG GIT lub "nie wymagany"]

### Cel

[Jedno zdanie opisujące co ma zostać osiągnięte]

### Kontekst

[Dlaczego to robimy, co było wcześniej, jakie decyzje podjęto]

### Zakres

**W zakresie (DO)**:
- [ ] [Konkretne zadanie 1]
- [ ] [Konkretne zadanie 2]

**Poza zakresem (NIE RÓB)**:
- [Czego worker MA NIE robić]

### Pliki do modyfikacji

| Plik | Oczekiwana zmiana |
|---|---|
| `app/...` | [opis zmiany] |

### Kryteria akceptacji

- [ ] [Warunek 1 — np. "endpoint /X zwraca 200"]
- [ ] [Warunek 2 — np. "brak błędów w konsoli JS"]
- [ ] [Warunek 3 — np. "CHANGELOG.md zaktualizowany"]

### Ograniczenia

- [np. "Nie modyfikuj webhook.py"]
- [np. "Zachowaj kompatybilność z Python 3.14"]

### Notatki

[Dodatkowe uwagi, linki, kontekst]

---

**Status**: ⬜ Do wykonania / 🔄 W trakcie / ✅ Wykonane / ❌ Odrzucone
