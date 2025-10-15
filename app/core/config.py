from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "WagnerFit Backend"
    debug: bool = True
    version: str = "0.1.0"

    # Supabase
    supabase_url: str | None = None
    supabase_service_key: str | None = None
    supabase_jwks_url: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str | None = None

    # Stripe
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    # Misc
    log_level: str = "INFO"
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
