"""Tests for the fuzzy field mapping engine."""
from app.mapping_ai import suggest_mapping, _similarity, _normalize


class TestNormalize:
    def test_strips_special_chars(self):
        assert _normalize("W-czym-możemy-pomóc-") == "w czym możemy pomóc"

    def test_underscores_to_spaces(self):
        assert _normalize("full_name") == "full name"


class TestSimilarity:
    def test_exact_match(self):
        assert _similarity("email", "email") == 1.0

    def test_synonym_match(self):
        score = _similarity("phone_number", "Telefon")
        assert score >= 0.9

    def test_email_synonym(self):
        score = _similarity("email", "E-mail")
        assert score >= 0.9

    def test_name_synonym(self):
        score = _similarity("full_name", "Imie-i-nazwisko")
        assert score >= 0.9

    def test_unrelated_fields(self):
        score = _similarity("email", "Zyczenie")
        assert score < 0.5


class TestSuggestMapping:
    FB_QUESTIONS = [
        {"key": "full_name", "label": "Full Name"},
        {"key": "phone_number", "label": "Phone Number"},
        {"key": "email", "label": "Email"},
        {"key": "w_czym_mozemy_pomoc", "label": "W czym możemy pomóc?"},
        {"key": "dodatkowa_informacja", "label": "Dodatkowa informacja"},
    ]

    MD_FIELDS = [
        {"fieldId": "Imie-i-nazwisko", "name": "Imię i Nazwisko"},
        {"fieldId": "Telefon", "name": "Telefon"},
        {"fieldId": "E-mail", "name": "E-mail"},
        {"fieldId": "W-czym-mozemy-pomoc-", "name": "W czym możemy pomóc?"},
        {"fieldId": "Dodatkowa-informacja", "name": "Dodatkowa informacja"},
        {"fieldId": "zgoda", "name": "Wyrażam zgodę"},
    ]

    def test_maps_most_fields(self):
        suggestions = suggest_mapping(self.FB_QUESTIONS, self.MD_FIELDS)
        assert len(suggestions) >= 4  # should map at least 4 of 5

    def test_name_mapped_correctly(self):
        suggestions = suggest_mapping(self.FB_QUESTIONS, self.MD_FIELDS)
        name_map = next((s for s in suggestions if s.fb_field == "full_name"), None)
        assert name_map is not None
        assert name_map.medidesk_field == "Imie-i-nazwisko"

    def test_email_mapped_correctly(self):
        suggestions = suggest_mapping(self.FB_QUESTIONS, self.MD_FIELDS)
        email_map = next((s for s in suggestions if s.fb_field == "email"), None)
        assert email_map is not None
        assert email_map.medidesk_field == "E-mail"

    def test_phone_mapped_correctly(self):
        suggestions = suggest_mapping(self.FB_QUESTIONS, self.MD_FIELDS)
        phone_map = next((s for s in suggestions if s.fb_field == "phone_number"), None)
        assert phone_map is not None
        assert phone_map.medidesk_field == "Telefon"

    def test_confidence_scores_present(self):
        suggestions = suggest_mapping(self.FB_QUESTIONS, self.MD_FIELDS)
        for s in suggestions:
            assert 0.0 < s.confidence <= 1.0

    def test_no_duplicates(self):
        suggestions = suggest_mapping(self.FB_QUESTIONS, self.MD_FIELDS)
        md_fields = [s.medidesk_field for s in suggestions]
        assert len(md_fields) == len(set(md_fields))  # no duplicates

    def test_empty_input(self):
        result = suggest_mapping([], [])
        assert result == []
