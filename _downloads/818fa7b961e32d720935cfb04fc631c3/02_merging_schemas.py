"""
Merging Schemas
===============

In this example, we will demonstrate how to merge multiple schemas

"""

import inspect
from pathlib import Path

import yaml

from elphick.pandera_utils.pandera_utils import load_schema_from_yaml, merge_schemas
from elphick.pandera_utils.utils.pandera_io_pandas_io import to_yaml

__file__ = Path(inspect.getfile(inspect.currentframe())).resolve()


def print_schemafile(filepath: Path):
    with open(filepath, "r", encoding="utf-8") as f:
        schema_yaml = yaml.safe_load(f)
        print(yaml.dump(schema_yaml, sort_keys=False, indent=2))


# %%
# Load Schemas
# ------------
# Load and view the schemas from the YAML files

schema_filepath_1: Path = __file__.parents[1] / "assets/aliases_schema.yaml"
schema_filepath_2: Path = __file__.parents[1] / "assets/category_schema.yaml"
schema_filepath_3: Path = __file__.parents[1] / "assets/missing_sentinels_schema.yaml"

# %%
print_schemafile(schema_filepath_1)

# %%
print_schemafile(schema_filepath_2)

# %%
print_schemafile(schema_filepath_3)

# %%
# Merge Schemas
# -------------
# Merge the schemas into a single schema

schema_1 = load_schema_from_yaml(schema_filepath_1)
schema_2 = load_schema_from_yaml(schema_filepath_2)
schema_3 = load_schema_from_yaml(schema_filepath_3)
merged_schema = merge_schemas([schema_1, schema_2, schema_3])
# %%
# Print the merged schema in a nicely formatted way
# use a temp file (formatting workaround only)
print(to_yaml(merged_schema))
