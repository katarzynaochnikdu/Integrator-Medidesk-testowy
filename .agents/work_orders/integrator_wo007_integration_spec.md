# 📋 Work Order #007

**Data**: 2026-06-03
**Worker**: 📝 Technical Writer / Documentation Keeper
**Priorytet**: 🟡 Normalny
**Snapshot**: nie wymagany (tylko dokumentacja)

### Cel

Stworzyć **samodzielny, przekazywalny** plik specyfikacji „jak wdrożyć dokładnie to, co testujemy" — do wysłania innemu systemowi/zespołowi.

### Kontekst

Użytkownik musi przekazać innemu systemowi wytyczne: gdzie jest dokumentacja i jak to ma działać. Istniejące pliki się nie nadają jako samodzielne wytyczne (`captcha_diagnoza.md` = w dużej części historia; `README.md` = config naszej apki; PDF = stary w części reCAPTCHA). Potrzebny jeden kanoniczny, aktualny dokument.

### Zakres

**W zakresie (DO)**:
- [x] `docs/INTEGRACJA_MEDIDESK.md` — kontrakt (GET/POST na UUID, body, captcha header `enterprise-recaptcha-response`, site-key `6Ldo-f0s…`, odpowiedzi 200/400/500), przykład `kochnikmini`, referencja na żywo `/demo/contact` + pliki kodu, ENV, „czego NIE robić".
- [x] `docs/CHANGELOG.md` — wpis.

**Poza zakresem (NIE RÓB)**:
- NIE zmieniać kodu/configu (wartości captchy = ENV, zarządza użytkownik).

### Kryteria akceptacji

- [x] Plik samodzielny (można przesłać bez reszty repo), aktualne wartości, nadrzędny nad starym PDF.
- [x] Przykład 1:1 z tym, co testujemy (`e8342a6a` / kochnikmini).
- [x] `docs/CHANGELOG.md` zaktualizowany.
- [x] 📝 **DocGate**: PASS — `.agents/doc_reports/integrator_wo007_integration_spec.md`
- [—] 🛡 SecGate: N/D (brak kodu).

### Notatki

- Do przekazania: plik `docs/INTEGRACJA_MEDIDESK.md` + URL referencji `https://md-integrator-old.onrender.com/demo/contact`.

---

**Status**: ✅ Wykonane — DocGate PASS (brak kodu → SecGate N/D)
