"""
Export utilities for writing schema definitions from the registry database
back into pandera-compatible dictionary or YAML representations.

This module reconstructs the logical schema structure from the database
models defined in :mod:`pandera_utils.registry.models`, including the original
source filename stored in :class:`SchemaSource`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml
from sqlalchemy.orm import Session

from .models import Schema


def export_schema_dict(session: Session, schema_name: str) -> Dict[str, Any]:
    """Export a schema from the registry as a pandera-compatible dictionary.

    Args:
        session: Active SQLAlchemy session.
        schema_name: Name of the schema to export.

    Returns:
        A dictionary suitable for constructing a ``pandera.DataFrameSchema``.

    Raises:
        LookupError: If no schema with the given name exists.
    """
    schema = (
        session.query(Schema)
        .filter(Schema.name == schema_name)
        .one_or_none()
    )
    if schema is None:
        raise LookupError(f"Schema '{schema_name}' not found in registry")

    # Assemble field definitions.
    fields = {}
    for sf in schema.fields:
        variable = sf.variable

        field_meta = {
            "dtype": variable.data_type,
            "nullable": variable.nullable,
            "required": sf.required,
            "description": variable.description,
        }

        # Merge variable-level metadata (shared)
        if variable.metadata:
            field_meta.update(variable.metadata)

        # Merge schema-field-level metadata (overrides)
        if sf.metadata:
            field_meta.update(sf.metadata)

        fields[variable.name] = field_meta

    schema_dict = {
        "name": schema.name,
        "description": schema.description,
        "category": schema.category,
        "metadata": schema.metadata,
        "fields": fields,
    }

    return schema_dict


def export_schema_yaml(
    session: Session,
    schema_name: str,
    output_path: Path | None = None,
) -> Path:
    """Export a schema to a YAML file, using original source filename if available.

    Args:
        session: Active SQLAlchemy session.
        schema_name: Name of the schema to export.
        output_path: Optional override path. If not provided, the original
            YAML file path stored in :class:`SchemaSource` is used.

    Returns:
        The path where the YAML file was written.

    Raises:
        LookupError: If the schema does not exist.
        ValueError: If no output path is provided and the schema has no source.
    """
    schema = (
        session.query(Schema)
        .filter(Schema.name == schema_name)
        .one_or_none()
    )
    if schema is None:
        raise LookupError(f"Schema '{schema_name}' not found in registry")

    # Determine output target
    if output_path is None:
        if schema.source is None:
            raise ValueError(
                f"Schema '{schema_name}' has no SchemaSource; "
                f"output_path must be provided explicitly."
            )
        output_path = Path(schema.source.path)

    schema_dict = export_schema_dict(session, schema_name)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(schema_dict, f, sort_keys=False)

    return output_path