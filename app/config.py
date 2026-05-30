from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    medidesk_api_base: str = "https://app.medidesk.io/api/forms"
    recaptcha_site_key: str = ""   # ustaw przez MEDIDESK_RECAPTCHA_SITE_KEY na Render
    # URL strony, którą bridge otwiera do wygenerowania tokenu. Puste =
    # domyślnie https://app.medidesk.io/forms/{form_id} (domena Medideska,
    # na whiteliście ich site-key'a).
    recaptcha_bridge_url: str = ""
    http_timeout: float = 15.0
    default_site_domain: str = ""
    default_site_url: str = ""

    # --- Provider tokenów captcha (zob. app/captcha_provider.py) ---
    captcha_mode: str = "solver"        # solver | bridge | none
    captcha_api_key: str = ""           # clientKey CapSolvera (MEDIDESK_CAPTCHA_API_KEY)
    captcha_action: str = "submit"      # pageAction reCAPTCHA v3
    captcha_min_score: float = 0.3      # minimalny akceptowany score
    captcha_timeout: float = 60.0       # budżet czasu na solve (sekundy)

    model_config = {"env_prefix": "MEDIDESK_"}


settings = Settings()
