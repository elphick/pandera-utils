"""
Basic usage
===========

A simple example demonstrating how to use `pandera_utils`.

"""
import inspect

import pandas as pd
from pathlib import Path
import yaml
from elphick.pandera_utils.pandera_utils import load_schema_from_yaml, DataFrameMetaProcessor

__file__ = Path(inspect.getfile(inspect.currentframe())).resolve()

# %%
# Load Schema
# -----------
# Load the schema from the YAML file
yaml_path = __file__.parents[1] / "assets/example_schema.yaml"
schema = load_schema_from_yaml(yaml_path)

# Print the YAML file in a nicely formatted way
with open(yaml_path, "r", encoding="utf-8") as f:
    schema_yaml = yaml.safe_load(f)
    print(yaml.dump(schema_yaml, sort_keys=False, indent=2))

# %%
# Create a sample DataFrame
# -------------------------
dataframe = pd.DataFrame({
    "col1": [1, 2, 3],
    "column2": [0.546, 1.568, 2.578],
})

# preserve a copy for comparison later
dataframe_copy = dataframe.copy(deep=True)

dataframe
# %%
# Initialize
# ----------
# Initialize the DataFrameMetaProcessor with the schema
processor = DataFrameMetaProcessor(schema)

# %%
# Rename Aliases
# --------------
df_with_alias = processor.apply_rename_from_alias(dataframe)
df_with_alias

# %%
# Apply calculations
# ------------------
df_with_calculations = processor.apply_calculations(df_with_alias)
df_with_calculations

# %%
# Apply rounding
# --------------
df_with_decimals = processor.apply_rounding(df_with_calculations)
df_with_decimals

# %%
# One Step Preprocessing
# ----------------------
# Preprocess the DataFrame, with alias renaming, rounding, and calculations.
# If metadata: decimals is not null, the column will be rounded to that number of decimal places after the other
# preprocessing steps.
# When set to True, the round_before_calc argument will round the DataFrame before applying calculations,
# as well as after.
processed_df = processor.preprocess(dataframe_copy, round_before_calc=False)
processed_df

# %%
# We can check that the individual steps are equivalent to the one-step preprocessing
assert processed_df.equals(df_with_decimals)

# %%
# Validate
# --------
# Validate the DataFrame using Pandera
validated_df = processor.validate(processed_df)
validated_df
