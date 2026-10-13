from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    DEMO_MODE: bool = True
    DATABASE_URL: str = "sqlite:///./golden_hour_grid.db"

    # Local-only demo credentials
    DEMO_AMBULANCE_USERNAME: str = "ambulance.demo"
    DEMO_AMBULANCE_PASSWORD: str = "CHANGE_ME_BEFORE_LOCAL_DEMO"
    DEMO_HOSPITAL_USERNAME: str = "hospital.demo"
    DEMO_HOSPITAL_PASSWORD: str = "CHANGE_ME_BEFORE_LOCAL_DEMO"
    DEMO_HOSPITAL_ID: str = "demo-hospital-1"

    # Session and security settings
    SESSION_COOKIE_NAME: str = "ghg_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_TTL_MINUTES: int = 480
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_RATE_WINDOW_SECONDS: int = 300

    # Demo feed settings
    DEMO_FEED_ENABLED: bool = True
    DEMO_FEED_INTERVAL_SECONDS: int = 15

    # Optional local AI settings
    LOCAL_ASSISTANT_ENABLED: bool = False
    LOCAL_ASSISTANT_PROVIDER: str = "ollama"
    LOCAL_ASSISTANT_BASE_URL: str = "http://localhost:11434"
    LOCAL_ASSISTANT_MODEL: str = ""

    # Real Road Map and Google Routes API configuration
    GOOGLE_MAPS_BROWSER_API_KEY: str = ""
    GOOGLE_MAPS_ROUTES_API_KEY: str = ""
    GOOGLE_MAPS_ROUTING_PREFERENCE: str = "TRAFFIC_AWARE"
    GOOGLE_MAPS_TIMEOUT_SECONDS: int = 4
    MAP_PROVIDER: str = "auto"  # 'google', 'osm', or 'auto'
    ROUTING_PROVIDER: str = "auto"  # 'google', 'osrm', 'demo', or 'auto'


settings = Settings()
