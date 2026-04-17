"""Fuzzy field mapping between Facebook Lead Ads and Medidesk forms."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)

# Common synonyms/aliases for medical form fields (Polish & English)
SYNONYMS: dict[str, list[str]] = {
    "full_name": [
        "full_name", "fullname", "full name",
        "imie i nazwisko", "imie-i-nazwisko", "imię i nazwisko", "imię-i-nazwisko",
        "imię oraz nazwisko",
        "osoba", "osoba kontaktowa",
        "dane osobowe",
    ],
    "first_name": [
        "first_name", "firstname", "imie", "imię", "name",
    ],
    "last_name": [
        "last_name", "lastname", "nazwisko", "surname",
    ],
    "company": [
        "company", "company_name", "firma", "nazwa firmy", "nazwa_firmy",
        "nazwa placówki", "placowka", "placówka", "klinika", "przychodnia",
        "organization", "organisation", "instytucja",
    ],
    "email": [
        "email", "e-mail", "mail", "adres email", "adres e-mail", "e_mail",
    ],
    "phone": [
        "phone", "telefon", "phone_number", "tel", "numer telefonu",
        "numer_telefonu", "mobile", "komórka", "komorka",
    ],
    "message": [
        "message", "wiadomosc", "wiadomość", "dodatkowa informacja",
        "dodatkowa_informacja", "komentarz", "uwagi", "tresc", "treść",
        "zyczenie", "życzenie", "opis", "opis problemu",
    ],
    "topic": [
        "topic", "temat", "w czym możemy pomóc", "w_czym_mozemy_pomoc",
        "w-czym-możemy-pomóc-", "lista", "rodzaj", "usluga", "usługa",
        "specjalizacja", "rodzaj badania",
    ],
    "consent": [
        "consent", "zgoda", "wyrażam zgodę", "wyrazam-zgode",
        "wyrażam-zgodę-na-kontakt", "akceptacja", "rodo",
    ],
    "city": [
        "city", "miasto", "miejscowosc", "miejscowość",
    ],
}


def _normalize(text: str) -> str:
    """Normalize field name for comparison: lowercase, remove diacritics-ish, strip special chars."""
    text = text.lower().strip()
    text = re.sub(r"[_\-\.]+", " ", text)
    text = re.sub(r"[^a-ząćęłńóśźżA-ZĄĆĘŁŃÓŚŹŻ0-9 ]", "", text)
    return text.strip()


def _find_synonym_group(name: str) -> str | None:
    """Check if a normalized name belongs to a known synonym group.
    
    Uses exact match or full-word containment (not loose substring).
    """
    norm = _normalize(name)
    for group, synonyms in SYNONYMS.items():
        for syn in synonyms:
            nsyn = _normalize(syn)
            # Exact match
            if nsyn == norm:
                return group
    # Second pass: check if the full normalized name matches a synonym as whole words
    norm_words = set(norm.split())
    for group, synonyms in SYNONYMS.items():
        for syn in synonyms:
            nsyn = _normalize(syn)
            syn_words = set(nsyn.split())
            # All synonym words must be present in the name (word-level match)
            if len(syn_words) >= 2 and syn_words.issubset(norm_words):
                return group
    return None


def _similarity(a: str, b: str) -> float:
    """Calculate similarity between two field names (0.0–1.0)."""
    na, nb = _normalize(a), _normalize(b)

    # Exact match
    if na == nb:
        return 1.0

    # Check synonym groups
    group_a = _find_synonym_group(a)
    group_b = _find_synonym_group(b)
    if group_a and group_b and group_a == group_b:
        return 0.95

    # Penalize cross-group matches (e.g., company matching name group)
    if group_a and group_b and group_a != group_b:
        return 0.0

    # Fuzzy string matching
    return SequenceMatcher(None, na, nb).ratio()


@dataclass
class MappingSuggestion:
    fb_field: str
    medidesk_field: str
    confidence: float


def suggest_mapping(
    fb_questions: list[dict[str, Any]],
    medidesk_fields: list[dict[str, Any]],
    threshold: float = 0.4,
) -> list[MappingSuggestion]:
    """Suggest field mappings between FB Lead Ads questions and Medidesk form fields.

    Supports merging: if first_name + last_name exist but no full_name,
    both will be mapped to the same target full_name field.

    Args:
        fb_questions: List of FB form questions, each with at least 'key' or 'label'.
        medidesk_fields: List of Medidesk form fields, each with at least 'fieldId' and 'name'.
        threshold: Minimum similarity score to include in suggestions.

    Returns:
        List of mapping suggestions sorted by confidence (highest first).
    """
    suggestions: list[MappingSuggestion] = []
    used_medidesk: set[str] = set()

    # Extract FB field names
    fb_fields: list[tuple[str, str]] = []
    for q in fb_questions:
        key = q.get("key", q.get("name", q.get("label", "")))
        label = q.get("label", q.get("name", key))
        fb_fields.append((key, label))

    # Extract Medidesk field names
    md_fields: list[tuple[str, str]] = []
    for f in medidesk_fields:
        field_id = f.get("fieldId", f.get("field_id", ""))
        name = f.get("name", field_id)
        md_fields.append((field_id, name))

    # ── Merge detection: first_name + last_name → full_name target ──
    fb_keys = {k for k, _ in fb_fields}
    fb_groups = {_find_synonym_group(k) for k in fb_keys}

    has_first = "first_name" in fb_groups
    has_last = "last_name" in fb_groups
    has_full = "full_name" in fb_groups

    if has_first and has_last and not has_full:
        # Find the target full_name MD field
        full_name_md = None
        for md_id, md_name in md_fields:
            if _find_synonym_group(md_id) == "full_name" or _find_synonym_group(md_name) == "full_name":
                full_name_md = md_id
                break

        if full_name_md:
            # Map both first_name and last_name to the same MD field
            for fb_key, fb_label in fb_fields:
                group = _find_synonym_group(fb_key)
                if group == "first_name":
                    suggestions.append(MappingSuggestion(
                        fb_field=fb_key, medidesk_field=full_name_md, confidence=0.90,
                    ))
                elif group == "last_name":
                    suggestions.append(MappingSuggestion(
                        fb_field=fb_key, medidesk_field=full_name_md, confidence=0.90,
                    ))
            # Mark these FB fields and MD field as used
            used_fb_merge = {s.fb_field for s in suggestions}
            # Don't add full_name_md to used_medidesk — it's intentionally shared
    else:
        used_fb_merge = set()

    # ── Standard 1:1 matching for remaining fields ──
    scored_pairs: list[tuple[float, str, str, str, str]] = []
    for fb_key, fb_label in fb_fields:
        if fb_key in used_fb_merge:
            continue
        for md_id, md_name in md_fields:
            # Compare both key-to-id and label-to-name, take the best
            score = max(
                _similarity(fb_key, md_id),
                _similarity(fb_key, md_name),
                _similarity(fb_label, md_id),
                _similarity(fb_label, md_name),
            )
            if score >= threshold:
                scored_pairs.append((score, fb_key, fb_label, md_id, md_name))

    # Sort by score descending, greedily assign (each field used once)
    scored_pairs.sort(key=lambda x: x[0], reverse=True)
    used_fb: set[str] = set(used_fb_merge)

    # Block MD fields already used by merge
    merge_md_ids = {s.medidesk_field for s in suggestions}

    for score, fb_key, fb_label, md_id, md_name in scored_pairs:
        if fb_key in used_fb or md_id in used_medidesk or md_id in merge_md_ids:
            continue
        suggestions.append(MappingSuggestion(
            fb_field=fb_key,
            medidesk_field=md_id,
            confidence=round(score, 2),
        ))
        used_fb.add(fb_key)
        used_medidesk.add(md_id)

    suggestions.sort(key=lambda s: s.confidence, reverse=True)
    logger.info(
        "Mapping suggested %d/%d FB fields (threshold=%.2f)",
        len(suggestions), len(fb_fields), threshold,
    )
    return suggestions
