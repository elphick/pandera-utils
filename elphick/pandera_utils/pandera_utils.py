from collections import OrderedDict
from pathlib import Path
from typing import Optional

import pandas as pd
from pandera import DataFrameSchema

from elphick.pandera_utils.utils.pandera_io_pandas_io import from_yaml
import logging


def order_columns_to_match_schema(df: pd.DataFrame, schema: DataFrameSchema) -> pd.DataFrame:
    """Order DataFrame columns to match the schema order if coerce and metadata['order_columns'] are true.

    Columns not specified in the schema will be retained at the end of the DataFrame.
    Args:
        df: The DataFrame to reorder.
        schema: The Pandera DataFrameSchema defining the desired column order.

    Returns:
        A DataFrame with columns reordered to match the schema, retaining extra columns at the end.
    """
    # Check if both 'coerce' and 'order_columns' are true
    if schema.coerce and schema.metadata and schema.metadata.get('pandera_utils', {}).get("order_columns", False):
        schema_columns = list(schema.columns.keys())
        # Retain only columns present in the schema, in schema order
        reordered_columns = [col for col in schema_columns if col in df.columns]
        # Retain extra columns in their original order
        extra_columns = [col for col in df.columns if col not in schema_columns]
        return df[reordered_columns + extra_columns]
    return df


class DataFrameMetaProcessor:
    """A class to preprocess and validate DataFrames based on metadata."""

    def __init__(self, schema: DataFrameSchema):
        """Instantiate the DataFrameMetaProcessor object.

        Args:
            schema: The DataFrameSchema object to use for preprocessing and validation.
        """
        self.schema: DataFrameSchema = schema
        self.supported_column_meta_keys = ['unit_of_measure', 'aliases', 'decimals', 'missing_sentinels', 'category',
                                           'calculation']

    @property
    def unit_of_measure_map(self):
        return OrderedDict(
            (col_name, col.metadata.get('pandera_utils', {}).get('unit_of_measure'))
            for col_name, col in self.schema.columns.items()
            if col.metadata and 'pandera_utils' in col.metadata and 'unit_of_measure' in col.metadata['pandera_utils']
        )

    from collections import OrderedDict

    @property
    def alias_map(self):
        alias_dict = OrderedDict()
        for col_name, col in self.schema.columns.items():
            if col.metadata and 'pandera_utils' in col.metadata and 'aliases' in col.metadata['pandera_utils']:
                alias_dict[col_name] = col.metadata['pandera_utils']['aliases']
        return alias_dict

    @property
    def calculation_map(self):
        return OrderedDict(
            (col_name, col.metadata.get('pandera_utils', {}).get('calculation'))
            for col_name, col in self.schema.columns.items()
            if col.metadata and 'pandera_utils' in col.metadata and 'calculation' in col.metadata['pandera_utils']
        )

    @property
    def decimals_map(self):
        return OrderedDict(
            (col_name, col.metadata.get('pandera_utils', {}).get('decimals'))
            for col_name, col in self.schema.columns.items()
            if col.metadata and 'pandera_utils' in col.metadata and 'decimals' in col.metadata['pandera_utils']
        )

    @property
    def missing_sentinels_map(self):
        return OrderedDict(
            (col_name, col.metadata.get('pandera_utils', {}).get('missing_sentinels'))
            for col_name, col in self.schema.columns.items()
            if col.metadata and 'pandera_utils' in col.metadata and 'missing_sentinels' in col.metadata['pandera_utils']
        )

    @property
    def category_maps(self):
        cat_maps = OrderedDict(
            (col_name, col.metadata.get('pandera_utils', {}).get('category'))
            for col_name, col in self.schema.columns.items()
            if col.metadata and 'pandera_utils' in col.metadata and 'category' in col.metadata['pandera_utils']
        )
        return OrderedDict(
            (k, {sub_k: sub_v for sub_k, sub_v in v.items() if isinstance(sub_v, dict)})
            for k, v in cat_maps.items() if v
        )

    @property
    def category_ordered_map(self):
        return OrderedDict(
            (col_name, col.metadata.get('pandera_utils', {}).get('category', {}).get('ordered'))
            for col_name, col in self.schema.columns.items()
            if col.metadata and 'pandera_utils' in col.metadata and 'category' in col.metadata['pandera_utils']
        )

    def apply_rename_from_alias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns in the DataFrame based on aliases."""
        alias_map = self.alias_map
        rename_map = {}

        for col_name, aliases in alias_map.items():
            for alias in aliases:
                if alias in df.columns:
                    rename_map[alias] = col_name

        return df.rename(columns=rename_map)

    def apply_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply calculations based on the calculation metadata."""
        for col_name, calculation in self.calculation_map.items():
            # Check for input columns
            inputs = self.schema.columns[col_name].metadata['pandera_utils'].get('inputs', [])
            missing_columns = [dep for dep in inputs if dep not in df.columns]
            required = self.schema.columns[col_name].required

            if missing_columns:
                if required:
                    raise KeyError(f"Missing columns for calculation '{col_name}': {missing_columns}")
                else:
                    logging.warning(f"Missing columns for optional (non-required) calculation '{col_name}': {missing_columns}")
                    continue

            # Evaluate the calculation
            calculated_column = eval(calculation, {}, df.to_dict('series'))

            # Determine the position to insert the calculated column
            if inputs:
                rightmost_input = max(df.columns.get_loc(dep) for dep in inputs)
                df.insert(rightmost_input + 1, col_name, calculated_column)
            else:
                df[col_name] = calculated_column

        return df

    def apply_rounding(self, df: pd.DataFrame, columns: Optional[list[str]] = None) -> pd.DataFrame:
        """Round columns based on the decimals metadata."""
        if columns is None:
            columns = self.decimals_map.keys()
        for col_name in columns:
            if col_name in self.decimals_map and col_name in df.columns:
                df[col_name] = df[col_name].round(self.decimals_map[col_name])
        return df

    def _generate_category_columns(self, column: pd.Series, map_dict: dict,
                                   retain_original_column: bool = True) -> dict:
        """Generate new columns based on the category metadata."""
        new_columns = {}
        schema_column = self.schema.columns[column.name]

        if retain_original_column:
            # Retrieve allowable categories
            allowable_categories = None
            if 'checks' in schema_column.__dict__:
                for check in schema_column.__dict__['checks']:
                    if check.name == 'isin':
                        allowable_categories = list(check._check_kwargs['allowed_values'])
                        break

            new_columns[column.name] = column.astype(pd.CategoricalDtype(categories=allowable_categories,
                                                                         ordered=self.category_ordered_map.get(
                                                                             column.name, False)))

        for k, v in map_dict.items():
            new_columns[f"{column.name}_{k}"] = column.map(v['map']).astype(v['dtype'])

        return new_columns

    def apply_missing_sentinels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply missing sentinels based on the missing_sentinels metadata."""
        for col_name, sentinels in self.missing_sentinels_map.items():
            if col_name in df.columns:
                df[col_name] = self.schema.columns[col_name].validate(df[[col_name]])
                df[col_name] = df[col_name].replace(sentinels, pd.NA)
        return df

    def apply_category_maps(self, df: pd.DataFrame, maps_to_apply: Optional[list[str]] = None,
                            retain_orig_cat_col: bool = True) -> pd.DataFrame:
        """Apply category maps to create new columns based on the category metadata."""
        # assert the supplied maps are valid
        all_map_keys: list[str] = list(self.category_maps[list(self.category_maps.keys())[0]].keys())

        if maps_to_apply is not None:
            for map_name in maps_to_apply:
                assert map_name in all_map_keys, f"Map name '{map_name}' not found in category_map"
        else:
            maps_to_apply = all_map_keys

        # Apply the maps
        for col in self.category_maps.keys():
            if col not in df.columns and self.schema.columns[col].required == True:
                raise KeyError(f"Column '{col}' not found in DataFrame")
            original_col_position = df.columns.get_loc(col)
            new_columns = self._generate_category_columns(df[col], self.category_maps[col], retain_orig_cat_col)

            # Insert columns at the original position, and to the right of the original
            for col_name, col_data in new_columns.items():
                if col_name == col:
                    df[col_name] = col_data
                else:
                    original_col_position += 1
                    df.insert(original_col_position, col_name, col_data)

        return df

    def preprocess(self, df: pd.DataFrame, round_before_calc: bool = False,
                   cat_maps_to_apply: Optional[list[str]] = None, cat_retain_orig_cat_col: bool = True) -> pd.DataFrame:
        """Preprocess a DataFrame based on the metadata.

        Args:
            df: The DataFrame to preprocess.
            round_before_calc: A boolean indicating whether to round columns before applying calculations,
            as well as after.
            cat_maps_to_apply: A list of category maps to apply. If None, all maps will be applied.
            cat_retain_orig_cat_col: A boolean indicating whether to retain the original category columns.
        """

        # Check for DataFrame-level metadata for column ordering
        if self.schema.metadata and self.schema.metadata.get('pandera_utils', {}).get("order_columns", False):
            df = order_columns_to_match_schema(df, self.schema)

        if self.alias_map:
            df = self.apply_rename_from_alias(df)
        if self.missing_sentinels_map:
            df = self.apply_missing_sentinels(df)

        # Handle rounding before calculations if specified
        if round_before_calc and self.decimals_map:
            df = self.apply_rounding(df)

        # Determine all inputs for calculated columns
        calculation_inputs = {
            dep for col, calc in self.calculation_map.items()
            for dep in self.schema.columns[col].metadata['pandera_utils'].get('inputs', [])
        }

        # Process each column
        for col in self.schema.columns.keys():
            if col in self.calculation_map:
                # Perform calculations
                df = self.apply_calculations(df)

            # Skip rounding for columns that are inputs of calculated columns
            if not round_before_calc and col in self.decimals_map and col not in self.calculation_map and col not in calculation_inputs:
                df = self.apply_rounding(df, columns=[col])

            if col in self.category_maps:
                df = self.apply_category_maps(df, maps_to_apply=cat_maps_to_apply,
                                              retain_orig_cat_col=cat_retain_orig_cat_col)

        # Apply rounding after calculations if needed
        if not round_before_calc and self.decimals_map:
            df = self.apply_rounding(df)

        # Last chance column ordering
        if self.schema.metadata and self.schema.metadata.get('pandera_utils', {}).get("order_columns", False):
            df = order_columns_to_match_schema(df, self.schema)

        return df

    def validate(self, df: pd.DataFrame, return_calculated_columns: bool = True) -> pd.DataFrame:
        """Validate a DataFrame based on the schema."""
        df = self.schema.validate(df)
        if not return_calculated_columns:
            return df.drop(columns=list(self.calculation_map.keys()))
        return df

    def check_schema(self):
        """Check if the schema is valid."""

        # Check the aliases are all unique
        alias_map = self.alias_map
        all_aliases = [alias for aliases in alias_map.values() for alias in aliases]
        duplicate_aliases = {alias for alias in all_aliases if all_aliases.count(alias) > 1}
        if duplicate_aliases:
            raise ValueError(f"Duplicate aliases found: {duplicate_aliases}")

        # Check that all alias keys are a list of strings
        for col_name, aliases in alias_map.items():
            for alias in aliases:
                if not isinstance(alias, str):
                    raise TypeError(
                        f"Alias '{alias}' in column '{col_name}' is not a string. All alias keys must be strings.")

        # Check all columns with metadata.category values (maps) have the same keys
        category_maps = self.category_maps
        if category_maps:
            # Get the set of keys from the first column's category map
            reference_keys = set(next(iter(category_maps.values())).keys())
            for col_name, category_map in category_maps.items():
                if set(category_map.keys()) != reference_keys:
                    raise ValueError(
                        f"Inconsistent category map keys in column '{col_name}'. "
                        f"Expected keys: {reference_keys}, but got: {set(category_map.keys())}."
                    )


def load_schema_from_yaml(yaml_path: Path) -> DataFrameSchema:
    """Load a DataFrameSchema from a YAML file."""
    return from_yaml(yaml_path)


def merge_schemas(list_of_schemas: list[DataFrameSchema]) -> DataFrameSchema:
    """Merge a list of DataFrameSchemas into a single DataFrameSchema.

    The merged schema will contain all columns and checks from the input schemas.
    The schema for root level properties or the index will be taken from the first schema in the list.
    If there are multiple columns defined, the column from the first schema in the list will be used.

    Args:
        list_of_schemas:  The list of DataFrameSchemas to merge.

    Returns:
        A DataFrameSchema that combines all the input schemas.
    """
    if not list_of_schemas:
        raise ValueError("The list of schemas is empty")

    # Start with the first schema
    base_schema = list_of_schemas[0]

    # Merge columns
    merged_columns = base_schema.columns.copy()
    for schema in list_of_schemas[1:]:
        for col_name, col in schema.columns.items():
            if col_name not in merged_columns:
                merged_columns[col_name] = col

    # Merge checks
    merged_checks = base_schema.checks.copy()
    for schema in list_of_schemas[1:]:
        for check in schema.checks:
            if check not in merged_checks:
                merged_checks.append(check)

    # Create the merged schema
    merged_schema = DataFrameSchema(
        columns=merged_columns,
        checks=merged_checks,
        index=base_schema.index,
        dtype=base_schema.dtype,
        coerce=base_schema.coerce,
        strict=base_schema.strict,
        name=base_schema.name,
        ordered=base_schema.ordered,
        unique=base_schema.unique,
        report_duplicates=base_schema.report_duplicates,
        unique_column_names=base_schema.unique_column_names,
        add_missing_columns=base_schema.add_missing_columns,
        title=base_schema.title,
        description=base_schema.description,
    )

    return merged_schema


def load_merged_schema_from_yaml(yaml_paths: list[Path]) -> DataFrameSchema:
    """Load and merge DataFrameSchemas from a list of YAML files."""
    schemas = [load_schema_from_yaml(yaml_path) for yaml_path in yaml_paths]
    return merge_schemas(schemas)
