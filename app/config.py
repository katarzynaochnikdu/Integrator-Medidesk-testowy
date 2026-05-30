from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    medidesk_api_base: str = "https://app.medidesk.io/api/forms"
    recaptcha_site_key: str = ""   # ustaw przez MEDIDESK_RECAPTCHA_SITE_KEY na Render
    http_timeout: float = 15.0
    default_site_domain: str = ""
    default_site_url: str = ""

    model_config = {"env_prefix": "MEDIDESK_"}


settings = Settings()
