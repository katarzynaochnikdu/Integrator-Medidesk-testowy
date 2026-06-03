# 📋 Work Order #006

**Data**: 2026-06-03
**Worker**: 📝 Technical Writer / Documentation Keeper
**Priorytet**: 🟡 Normalny
**Snapshot**: nie wymagany (tylko dokumentacja, brak kodu)

### Cel

Ujednoznacznić w dokumentacji **aktualny kontrakt captchy** (nadrzędny nad PDF spec, który w części reCAPTCHA jest stary) i poprawić zdezaktualizowany endpoint POST w README.

### Kontekst

Info od Medideska (2026-06-03): poprawny strzał = **UUID + token**; **500 = brak/zły token**; `webFormId`/`string` niezgodne z dokumentacją. Wartości captchy **po naszej stronie są nowe/aktualne** (`enterprise-recaptcha-response`, site-key `6Ldo-f0s…`), a te w PDF spec (`captcha-response`, `6Lfs81gh…`, zwykła v3) są **stare**. Dane trzymane w **ENV** — użytkownik zarządza nimi sam, kodu/configu NIE zmieniamy.

### Zakres

**W zakresie (DO)**:
- [ ] `docs/captcha_diagnoza.md` — baner „AKTUALNY KONTRAKT" (nadrzędny nad PDF); oznaczenie sekcji 0–4 jako historia.
- [ ] `docs/README.md` — endpoint POST `{webFormId}` → `{formTemplateId}` (UUID, WO#004).
- [ ] `pliki od medidesk/_UWAGA-aktualnosc-captcha.md` — notatka, że sekcja reCAPTCHA w PDF jest nieaktualna.
- [ ] `docs/CHANGELOG.md` — wpis.

**Poza zakresem (NIE RÓB)**:
- NIE zmieniać `app/config.py` ani kodu — wartości captchy to zmienne środowiskowe (zarządza użytkownik).
- NIE edytować samego PDF-a (artefakt Medideska) — tylko dodać notatkę obok.
- NIE przepisywać historii w `captcha_diagnoza.md` (sekcje 0–4 zostają jako zapis).

### Kryteria akceptacji

- [x] Docs jasno wskazują aktualne wartości (`enterprise-recaptcha-response`, `6Ldo-f0s…`) jako nadrzędne nad PDF.
- [x] README pokazuje POST na UUID (`formTemplateId`).
- [x] `docs/CHANGELOG.md` zaktualizowany.
- [x] 📝 **DocGate**: PASS — `.agents/doc_reports/integrator_wo006_doc_captcha_contract.md`
- [—] 🛡 SecGate: N/D (brak kodu).

### Notatki

- Klasyfikacja: „tylko dokumentacja" → bez snapshotu, bez SecGate (reguła Master).

---

**Status**: ✅ Wykonane — DocGate PASS (brak kodu → SecGate N/D)
