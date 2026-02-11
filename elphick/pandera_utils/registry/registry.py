"""
High-level schema registry API.

This module exposes the :class:`SchemaRegistry` class, which provides a
convenient interface for:

* Initializing a registry backed by a relational database.
* Importing pandera YAML schema files into the registry.
* Rebuilding the registry from a set of YAML files (treating the DB
  as a derived artefact).
* Exporting schemas back to pandera-compatible dictionaries or YAML.

The database URL and other options can be provided directly or loaded
from a small YAML configuration file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .importer import import_yaml_schemas
from .exporter import export_schema_dict, export_schema_yaml
from .models import Base


class SchemaRegistry:
    """Schema registry for managing pandera schemas in a relational database.

    This class wraps lower-level importer/exporter functions and provides
    a simple interface for working with YAML schema files and DB-backed
    representations.

    Typical usage example:
        from pathlib import Path
        from pandera_utils.registry import SchemaRegistry

        config_path = Path("config/registry.yaml")
        registry = SchemaRegistry.from_yaml(config_path)

        yaml_files = [Path("schemas/orders.yaml"), Path("schemas/customers.yaml")]
        registry.rebuild_from_yaml(yaml_files)

        orders_schema = registry.export_schema_dict("orders")

    The configuration YAML is expected to contain at least a ``db_url`` key,
    for example::

        db_url: "sqlite:///./.cache/registry.sqlite"
    """

    def __init__(self, db_url: str, *, echo: bool = False) -> None:
        """Initialize a SchemaRegistry instance.

        Args:
            db_url: SQLAlchemy database URL
                (e.g. ``sqlite:///./.cache/registry.sqlite``).
            echo: Whether to enable SQLAlchemy engine echo (SQL logging).
        """
        self._db_url = db_url
        self._engine = create_engine(self._db_url, echo=echo)
        self._SessionFactory = sessionmaker(bind=self._engine)

        Base.metadata.create_all(self._engine)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_config(cls, config: RegistryConfig) -> "SchemaRegistry":
        """Create a SchemaRegistry from a RegistryConfig instance.

        Args:
            config: RegistryConfig object containing database settings.

        Returns:
            Initialized :class:`SchemaRegistry` instance.
        """
        return cls(db_url=config.db_url, echo=config.echo)

    @classmethod
    def from_yaml(cls, config_path: Path) -> "SchemaRegistry":
        """Create a SchemaRegistry from a YAML configuration file.

        The config must contain at least a ``db_url`` key, for example::

            db_url: "sqlite:///./.cache/registry.sqlite"

        Args:
            config_path: Path to the registry YAML config file.

        Returns:
            Initialized :class:`SchemaRegistry` instance.

        Raises:
            FileNotFoundError: If the config file does not exist.
            KeyError: If ``db_url`` is missing from the config.
            ValueError: If the YAML cannot be parsed.
        """
        if not config_path.exists():
            raise FileNotFoundError(config_path)

        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in config: {config_path}") from exc

        try:
            db_url = config["db_url"]
        except KeyError as exc:
            raise KeyError("Missing required 'db_url' in registry config") from exc

        return cls(db_url=db_url)

    # ------------------------------------------------------------------
    # Session helper
    # ------------------------------------------------------------------
    def _session(self) -> Session:
        """Create a new SQLAlchemy session.

        Returns:
            A new :class:`sqlalchemy.orm.Session` instance.
        """
        return self._SessionFactory()

    # ------------------------------------------------------------------
    # Import operations
    # ------------------------------------------------------------------
    def rebuild_from_yaml(self, yaml_paths: Iterable[Path]) -> None:
        """Drop and recreate all tables, then import the given YAML schemas.

        This method treats the database as a *derived artefact*:
        the YAML files are considered the source of truth. Any existing
        registry contents will be discarded and replaced by the schemas
        defined in ``yaml_paths``.

        Args:
            yaml_paths: Iterable of YAML schema file paths to import.

        Raises:
            FileNotFoundError: If any of the YAML files do not exist.
            ValueError: If a YAML file is invalid or cannot be parsed.
        """
        yaml_paths = list(yaml_paths)
        missing = [p for p in yaml_paths if not p.exists()]
        if missing:
            missing_str = ", ".join(str(p) for p in missing)
            raise FileNotFoundError(f"Missing YAML schema files: {missing_str}")

        # Reset the database schema.
        Base.metadata.drop_all(self._engine)
        Base.metadata.create_all(self._engine)

        session = self._session()
        try:
            import_yaml_schemas(session, yaml_paths)
        finally:
            session.close()

    def import_yaml(self, yaml_paths: Iterable[Path]) -> None:
        """Import additional YAML schemas into the existing registry.

        This method does not drop any tables or clear existing data; it
        simply ingests the given YAML schemas and merges/updates them in
        the current database state.

        Args:
            yaml_paths: Iterable of YAML schema file paths to import.

        Raises:
            FileNotFoundError: If any of the YAML files do not exist.
            ValueError: If a YAML file is invalid or cannot be parsed.
        """
        yaml_paths = list(yaml_paths)
        missing = [p for p in yaml_paths if not p.exists()]
        if missing:
            missing_str = ", ".join(str(p) for p in missing)
            raise FileNotFoundError(f"Missing YAML schema files: {missing_str}")

        session = self._session()
        try:
            import_yaml_schemas(session, yaml_paths)
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Export operations
    # ------------------------------------------------------------------
    def export_schema_dict(self, schema_name: str) -> dict:
        """Export a schema as a pandera-compatible dictionary.

        Args:
            schema_name: Name of the schema to export.

        Returns:
            Dictionary representation suitable for constructing a
            :class:`pandera.DataFrameSchema`.

        Raises:
            LookupError: If the schema does not exist in the registry.
        """
        session = self._session()
        try:
            return export_schema_dict(session, schema_name)
        finally:
            session.close()

    def export_schema_yaml(
            self,
            schema_name: str,
            output_path: Path | None = None,
    ) -> Path:
        """Export a schema to a YAML file.

        If ``output_path`` is not provided, the original YAML path recorded
        in :class:`SchemaSource` (if any) is used as the target.

        Args:
            schema_name: Name of the schema to export.
            output_path: Optional override path for the YAML output.

        Returns:
            Path where the YAML file was written.

        Raises:
            LookupError: If the schema does not exist.
            ValueError: If no output path is provided and the schema has
                no associated :class:`SchemaSource`.
        """
        session = self._session()
        try:
            return export_schema_yaml(
                session=session,
                schema_name=schema_name,
                output_path=output_path,
            )
        finally:
            session.close()
