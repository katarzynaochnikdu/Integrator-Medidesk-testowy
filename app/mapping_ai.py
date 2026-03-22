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
    "name": ["imie", "imię", "nazwisko", "full_name", "imie-i-nazwisko", "imię-i-nazwisko", "osoba", "name", "fullname"],
    "email": ["email", "e-mail", "mail", "adres email", "adres e-mail", "e_mail"],
    "phone": ["phone", "telefon", "phone_number", "tel", "numer telefonu", "numer_telefonu", "mobile"],
    "message": ["message", "wiadomosc", "wiadomość", "dodatkowa informacja", "dodatkowa_informacja", "komentarz", "uwagi", "tresc", "treść", "zyczenie", "życzenie"],
    "topic": ["topic", "temat", "w czym możemy pomóc", "w_czym_mozemy_pomoc", "w-czym-możemy-pomóc-", "lista", "rodzaj", "usluga", "usługa"],
    "consent": ["consent", "zgoda", "wyrażam zgodę", "wyrazam-zgode", "wyrażam-zgodę-na-kontakt", "akceptacja", "rodo"],
}


def _normalize(text: str) -> str:
    """Normalize field name for comparison: lowercase, remove diacritics-ish, strip special chars."""
    text = text.lower().strip()
    text = re.sub(r"[_\-\.]+", " ", text)
    text = re.sub(r"[^a-ząćęłńóśźżA-ZĄĆĘŁŃÓŚŹŻ0-9 ]", "", text)
    return text.strip()


def _find_synonym_group(name: str) -> str | None:
    """Check if a normalized name belongs to a known synonym group."""
    norm = _normalize(name)
    for group, synonyms in SYNONYMS.items():
        for syn in synonyms:
            if _normalize(syn) == norm or norm in _normalize(syn) or _normalize(syn) in norm:
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

    # For each FB field, find best matching Medidesk field
    scored_pairs: list[tuple[float, str, str, str, str]] = []
    for fb_key, fb_label in fb_fields:
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
    used_fb: set[str] = set()

    for score, fb_key, fb_label, md_id, md_name in scored_pairs:
        if fb_key in used_fb or md_id in used_medidesk:
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
