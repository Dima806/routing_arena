"""Typed settings loaded from config/settings.yaml via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"


class VRPConfig(BaseModel):
    """VRP instance parameters for notebook 05 and the fleet dispatcher."""

    num_customers: int = 20
    num_vehicles: int = 4
    vehicle_capacity: int = 50
    demand_low: int = 1
    demand_high: int = 10


class Settings(BaseSettings):
    """Project-wide knobs: instance sizes, budgets, geometry, and seeds."""

    model_config = SettingsConfigDict(yaml_file=str(_CONFIG_PATH), extra="ignore")

    seed: int = 42
    tsp_sizes: list[int] = Field(default_factory=lambda: [5, 8, 10, 12, 15, 20, 30, 50])
    brute_force_max_n: int = 10
    layouts: list[str] = Field(default_factory=lambda: ["uniform", "clustered"])
    coordinate_range: float = 100.0
    num_clusters: int = 4
    time_budget_seconds: float = 5.0
    vrp: VRPConfig = Field(default_factory=VRPConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Read values from the YAML file, falling back to the defaults above."""
        return (init_settings, YamlConfigSettingsSource(settings_cls))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load (and cache) the project settings."""
    return Settings()
