from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.medidesk_client import MedideskResult, FormField, FormDefinition

client = TestClient(app)

FORM_ID = "d908ee01-0b7d-44a0-a494-a707ab5a55ef"
VALID_PAYLOAD = {
    "Imie-i-nazwisko": "Jan Kowalski",
    "Mail": "jan@test.pl",
    "Telefon": "+48500600700",
    "Lista": "Opcja 1",
    "zgoda": "true",
}


class TestRoot:
    def test_root_redirects_to_login(self):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert resp.headers["location"].startswith("/login")

    def test_api_info_returns_service(self):
        resp = client.get("/api/info")
        assert resp.status_code == 200
        assert "Integracja Leadów do Medidesk" in resp.json()["service"]


class TestGetFormFields:
    @patch("app.main.fetch_form_definition", new_callable=AsyncMock)
    def test_returns_fields(self, mock_fetch):
        mock_fetch.return_value = FormDefinition(
            name="Test Form",
            fields=[
                FormField(field_id="Osoba", field_type="TEXT_FIELD", required=True, name="Osoba"),
                FormField(field_id="Mail", field_type="EMAIL", required=True, name="Mail"),
            ],
        )
        resp = client.get(f"/api/forms/{FORM_ID}/fields")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["fields"]) == 2
        assert data["fields"][0]["fieldId"] == "Osoba"
        assert data["form_name"] == "Test Form"
        assert data["web_form_id"] == ""

    @patch("app.main.fetch_form_definition", new_callable=AsyncMock)
    def test_returns_404_when_empty(self, mock_fetch):
        mock_fetch.return_value = None
        resp = client.get(f"/api/forms/{FORM_ID}/fields")
        assert resp.status_code == 404


class TestSubmitToMedidesk:
    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_success(self, mock_submit):
        mock_submit.return_value = MedideskResult(success=True, status_code=200)
        resp = client.post(f"/api/submit/{FORM_ID}", json=VALID_PAYLOAD)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_passes_form_id(self, mock_submit):
        mock_submit.return_value = MedideskResult(success=True, status_code=200)
        client.post(f"/api/submit/{FORM_ID}", json=VALID_PAYLOAD)
        args, kwargs = mock_submit.call_args
        assert args[0] == FORM_ID

    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_passes_field_values(self, mock_submit):
        mock_submit.return_value = MedideskResult(success=True, status_code=200)
        client.post(f"/api/submit/{FORM_ID}", json=VALID_PAYLOAD)
        args, kwargs = mock_submit.call_args
        assert args[1]["Imie-i-nazwisko"] == "Jan Kowalski"
        assert args[1]["zgoda"] == "true"

    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_validation_error(self, mock_submit):
        mock_submit.return_value = MedideskResult(
            success=False,
            status_code=400,
            body={
                "globalErrors": [],
                "fieldErrors": {"Telefon": [{"code": "format"}]},
            },
        )
        resp = client.post(f"/api/submit/{FORM_ID}", json=VALID_PAYLOAD)
        assert resp.status_code == 400
        assert resp.json()["status"] == "validation_error"

    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_upstream_error(self, mock_submit):
        mock_submit.return_value = MedideskResult(success=False, status_code=500)
        resp = client.post(f"/api/submit/{FORM_ID}", json=VALID_PAYLOAD)
        assert resp.status_code == 502
        assert resp.json()["status"] == "upstream_error"

    def test_empty_body(self):
        resp = client.post(f"/api/submit/{FORM_ID}", json={})
        assert resp.status_code == 400
        assert "No field values" in resp.json()["error"]

    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_site_domain_override(self, mock_submit):
        mock_submit.return_value = MedideskResult(success=True, status_code=200)
        payload = {**VALID_PAYLOAD, "siteDomain": "klinika.pl", "siteUrl": "/form"}
        client.post(f"/api/submit/{FORM_ID}", json=payload)
        args, kwargs = mock_submit.call_args
        assert "siteDomain" not in args[1]
        assert kwargs.get("site_domain") or args[2] == "klinika.pl"

    @patch("app.main.submit_form_urlencoded", new_callable=AsyncMock)
    def test_passes_captcha_response(self, mock_submit):
        mock_submit.return_value = MedideskResult(success=True, status_code=200)
        payload = {**VALID_PAYLOAD, "captchaResponse": "captcha-token"}
        client.post(f"/api/submit/{FORM_ID}", json=payload)
        args, kwargs = mock_submit.call_args
        assert "captchaResponse" not in args[1]
        assert kwargs["captcha_response"] == "captcha-token"


class TestBuildUrlencoded:
    def test_builds_correct_format(self):
        from app.medidesk_client import build_urlencoded_body

        body = build_urlencoded_body({"Osoba": "Jan Kowalski", "Mail": "jan@test.pl"})
        assert "fieldsValues[Osoba]=Jan%20Kowalski" in body
        assert "fieldsValues[Mail]=jan%40test.pl" in body
        assert "siteDomain=" in body

    def test_encodes_plus_in_phone(self):
        from app.medidesk_client import build_urlencoded_body

        body = build_urlencoded_body({"Telefon": "+48500600700"})
        assert "fieldsValues[Telefon]=%2B48500600700" in body

    def test_polish_diacritics_in_keys_and_values(self):
        """Field IDs are kept as RAW UTF-8 (not percent-encoded) because Medidesk's
        web-form parser doesn't decode `%C4%99` back to `ę` — it 500s on percent-
        encoded keys. Values stay percent-encoded (standard URL value encoding).
        Body is sent as UTF-8 bytes with charset=UTF-8 in Content-Type header."""
        from app.medidesk_client import build_urlencoded_body

        body = build_urlencoded_body({
            "Imię-i-nazwisko": "Łukasz Gęsty",
            "Załącznik": "Wyrażam zgodę",
        })
        # Key: raw Polish chars (NOT percent-encoded) so MD's parser sees the literal field name.
        assert "fieldsValues[Imię-i-nazwisko]=" in body
        assert "fieldsValues[Załącznik]=" in body
        # Encoding to UTF-8 must succeed (this is what we send to MD).
        encoded = body.encode("utf-8")
        assert b"Imi\xc4\x99-i-nazwisko" in encoded  # ę = C4 99 in UTF-8
        # Values keep percent-encoding (standard URL-value behavior).
        assert "%C5%81ukasz" in body and "G%C4%99sty" in body
        assert "Wyra%C5%BCam" in body and "zgod%C4%99" in body


class TestSubmitPostsToUuid:
    """Wysyłka idzie dokładnie jednym POST-em na UUID (formTemplateId).

    Zgodnie ze specyfikacją Medideska poprawny jest strzał na UUID + token;
    webFormId/string nie są używane (WO#004).
    """

    @patch("app.medidesk_client._post_once", new_callable=AsyncMock)
    def test_posts_only_to_uuid(self, mock_post):
        import asyncio
        from app.medidesk_client import submit_form_urlencoded

        mock_post.return_value = MedideskResult(success=True, status_code=200)

        # captcha_response podany wprost → pomija solver (brak sieci).
        result = asyncio.run(
            submit_form_urlencoded(FORM_ID, {"Mail": "jan@test.pl"}, captcha_response="tok")
        )

        assert result.success
        mock_post.assert_awaited_once()  # dokładnie jeden POST, nie dwa
        assert mock_post.await_args.args[0] == FORM_ID  # cel = UUID, nie webFormId


class TestDemoPage:
    def test_demo_disabled_by_default(self):
        resp = client.get("/demo/contact")
        assert resp.status_code == 404

    def test_demo_enabled(self, monkeypatch):
        monkeypatch.setattr(settings, "demo_page_enabled", True)
        resp = client.get("/demo/contact")
        assert resp.status_code == 200
        assert "Integracja Leadów do Medidesk" in resp.text
