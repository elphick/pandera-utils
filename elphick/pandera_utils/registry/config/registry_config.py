from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


DEFAULT_REGISTRY_CONFIG_PATH = Path("config/registry.yaml")


@dataclass
class RegistryConfig:
    """Configuration for the schema registry backend.

    Attributes:
        db_url: SQLAlchemy-compatible database URL, e.g.
            ``sqlite:///./.cache/registry.sqlite``.
        echo: Whether to enable SQLAlchemy engine echo (SQL logging).
    """

    db_url: str
    echo: bool = False


def load_registry_config(path: Path | None = None) -> RegistryConfig:
    """Load schema registry configuration from a YAML file.

    Args:
        path: Optional path to the YAML config. If not provided, a default
            location is used (``config/registry.yaml`` relative to CWD).

    Returns:
        Parsed :class:`RegistryConfig` instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML is invalid or required keys are missing.
    """
    if path is None:
        path = DEFAULT_REGISTRY_CONFIG_PATH

    if not path.exists():
        raise FileNotFoundError(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in registry config: {path}") from exc

    if "db_url" not in data:
        raise ValueError("Registry config missing required key: 'db_url'")

    return RegistryConfig(
        db_url=data["db_url"],
        echo=bool(data.get("echo", False)),
    )