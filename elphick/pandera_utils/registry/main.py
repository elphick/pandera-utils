"""
Example entry point for using the SchemaRegistry.

Run with:
    python -m pandera_utils.registry.main
"""

from __future__ import annotations

from pathlib import Path

from .registry import SchemaRegistry


def main() -> None:
    """Demonstrate basic SchemaRegistry usage.

    This script:

    1. Loads registry configuration from YAML.
    2. Rebuilds the registry database from a list of schema files.
    3. Exports a schema back to dict and YAML.

    Adjust paths as needed for your own project structure.
    """

    # Load config (uses default path config/registry.yaml if not provided)
    config = load_registry_config()

    # Build registry from config
    registry = SchemaRegistry.from_config(config)

    # YAML schema files to load
    yaml_files = [
        Path("schemas/orders.yaml"),
        Path("schemas/customers.yaml"),
    ]

    # Treat DB as derived — rebuild from YAML source of truth
    registry.rebuild_from_yaml(yaml_files)

    # Export a schema as dict
    orders_dict = registry.export_schema_dict("orders")
    print("Exported schema (dict):")
    print(orders_dict)

    # Export back to YAML (original filename by default)
    output_path = registry.export_schema_yaml("orders")
    print(f"Schema written to: {output_path}")


if __name__ == "__main__":
    main()
