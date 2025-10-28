# backend/settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:29092")
    KAFKA_TOPIC: str = Field(default="traffic_stream")
    ANOMALIES_TOPIC: str = Field(default="traffic.anomalies.v1")

    MONGO_URI: str = Field(default="mongodb://localhost:27018")
    MONGO_DB: str = Field(default="urban_insights")
    MONGO_COLLECTION: str = Field(default="metrics")

    EVENT_INTERVAL_MS: int = Field(default=300)

    # Configuración Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
