"""
Import utilities for loading pandera YAML schema files into the schema registry.

This module parses YAML schema definitions, normalizes them into the
database structure defined in :mod:`pandera_utils.registry.models`, and
persists them using a SQLAlchemy session.

Typical usage:

    from pathlib import Path
    from pandera_utils.registry.importer import import_yaml_schemas

    yaml_files = [Path("schemas/orders.yaml"), Path("schemas/customers.yaml")]
    import_yaml_schemas(session, yaml_files)

"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml
from sqlalchemy.orm import Session

from .models import Schema, SchemaField, SchemaSource, Variable


def import_yaml_schemas(
    session: Session,
    yaml_paths: Iterable[Path],
) -> None:
    """Import one or more YAML pandera schema files into the registry.

    This function treats each YAML file as representing a logical schema.
    The filename is stored in :class:`SchemaSource` so that the schema can be
    exported back to the same location later.

    Args:
        session: Active SQLAlchemy session.
        yaml_paths: Iterable of YAML schema file paths to import.

    Raises:
        FileNotFoundError: If any YAML file does not exist.
        ValueError: If a YAML structure is malformed.
    """
    for path in yaml_paths:
        if not path.exists():
            raise FileNotFoundError(path)

    for yaml_path in yaml_paths:
        raw = _load_yaml(yaml_path)

        schema = _import_single_schema(
            session=session,
            data=raw,
            source_path=yaml_path,
        )

        session.add(schema)

    # Commit only once after all imports for efficiency
    session.commit()


def _load_yaml(path: Path) -> dict:
    """Load a YAML file into a Python dictionary.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Parsed YAML content.

    Raises:
        ValueError: If the YAML cannot be parsed.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}") from exc


def _import_single_schema(
    session: Session,
    data: dict,
    source_path: Path,
) -> Schema:
    """Import a single schema definition into the database.

    Args:
        session: Active SQLAlchemy session.
        data: Parsed YAML dictionary for one schema.
        source_path: Path to the YAML file this schema came from.

    Returns:
        A populated :class:`Schema` instance (not yet committed).

    Raises:
        KeyError: If required YAML keys are missing.
        ValueError: If the YAML structure is invalid.
    """
    # --- Validate top-level keys ---
    try:
        schema_name = data["name"]
    except KeyError as exc:
        raise KeyError("YAML schema missing required key: 'name'") from exc

    # Optional fields
    schema_desc = data.get("description")
    schema_category = data.get("category")
    schema_metadata = data.get("metadata")

    # --- Load or create SchemaSource ---
    source = (
        session.query(SchemaSource)
        .filter(SchemaSource.path == str(source_path))
        .one_or_none()
    )
    if source is None:
        source = SchemaSource(path=str(source_path))
        session.add(source)
        session.flush()  # assigns source.id

    # --- Load or create Schema ---
    schema = (
        session.query(Schema)
        .filter(Schema.name == schema_name)
        .one_or_none()
    )
    if schema is None:
        schema = Schema(
            name=schema_name,
            description=schema_desc,
            category=schema_category,
            metadata=schema_metadata,
            source=source,
        )
        session.add(schema)
        session.flush()
    else:
        # Update metadata if provided
        schema.description = schema_desc or schema.description
        schema.category = schema_category or schema.category
        schema.metadata = schema_metadata or schema.metadata
        schema.source = source

        # Clear existing fields before reloading
        schema.fields.clear()
        session.flush()

    # --- Import fields ---
    fields_data = data.get("fields", {})
    if not isinstance(fields_data, dict):
        raise ValueError("YAML schema 'fields' must be a mapping")

    position = 0

    for field_name, field_data in fields_data.items():
        position += 1

        # Load or create the Variable (shared across schemas)
        variable = (
            session.query(Variable)
            .filter(Variable.name == field_name)
            .one_or_none()
        )
        if variable is None:
            variable = Variable(
                name=field_name,
                data_type=field_data["dtype"],
                description=field_data.get("description"),
                nullable=field_data.get("nullable", True),
                metadata=_extract_variable_metadata(field_data),
            )
            session.add(variable)
            session.flush()

        # Schema-specific field settings
        schema_field = SchemaField(
            schema=schema,
            variable=variable,
            position=position,
            required=field_data.get("required", True),
            metadata=_extract_schema_field_metadata(field_data),
        )
        session.add(schema_field)

    return schema


def _extract_variable_metadata(field_def: dict) -> dict:
    """Extract shared variable metadata from a YAML field definition.

    Args:
        field_def: Field definition from YAML.

    Returns:
        Dictionary of metadata to store on Variable.metadata.
    """
    return {
        "checks": field_def.get("checks"),
        "extra": field_def.get("extra"),
    }


def _extract_schema_field_metadata(field_def: dict) -> dict:
    """Extract schema-specific field metadata.

    Args:
        field_def: Field definition from YAML.

    Returns:
        Dictionary of metadata for SchemaField.metadata.
    """
    return {
        "alias": field_def.get("alias"),
        "default": field_def.get("default"),
    }