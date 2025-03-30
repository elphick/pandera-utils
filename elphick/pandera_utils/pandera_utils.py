from pathlib import Path

import yaml
from pandera import DataFrameSchema, Column, Check
from pandera.engines import pandas_engine
import pandas as pd
from pandera.io import _deserialize_check_stats


class DataFrameMetaProcessor:
    """A class to preprocess and validate DataFrames based on metadata."""
    def __init__(self, schema: DataFrameSchema):
        """Instantiate the DataFrameMetaProcessor object.

        Args:
            schema: The DataFrameSchema object to use for preprocessing and validation.
        """
        self.schema: DataFrameSchema = schema
        self.supported_column_meta_keys = ['alias', 'calculation', 'decimals']

    @property
    def alias_map(self):
        return {col.metadata['alias']: col_name for col_name, col in self.schema.columns.items() if
                col.metadata and 'alias' in col.metadata}

    @property
    def calculation_map(self):
        return {col_name: col.metadata['calculation'] for col_name, col in self.schema.columns.items() if
                col.metadata and 'calculation' in col.metadata}

    @property
    def decimals_map(self):
        return {col_name: col.metadata['decimals'] for col_name, col in self.schema.columns.items() if
                col.metadata and 'decimals' in col.metadata}

    def apply_rename_from_alias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns based on the alias metadata."""
        return df.rename(columns=self.alias_map)

    def apply_calculations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply calculations based on the calculation metadata."""
        for col_name, calculation in self.calculation_map.items():
            df[col_name] = eval(calculation, {}, df.to_dict('series'))
        return df

    def apply_rounding(self, df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
        """Round columns based on the decimals metadata."""
        if columns is None:
            columns = self.decimals_map.keys()
        for col_name in columns:
            if col_name in self.decimals_map and col_name in df.columns:
                df[col_name] = df[col_name].round(self.decimals_map[col_name])
        return df

    def preprocess(self, df: pd.DataFrame, round_before_calc: bool = False) -> pd.DataFrame:
        """Preprocess a DataFrame based on the metadata.

        Args:
            df: The DataFrame to preprocess.
            round_before_calc: A boolean indicating whether to round columns before applying calculations,
            as well as after.
        """
        df = self.apply_rename_from_alias(df)
        if round_before_calc:
            df = self.apply_rounding(df)
        df = self.apply_calculations(df)
        if not round_before_calc:
            df = self.apply_rounding(df)
        else:
            df = self.apply_rounding(df, columns=list(self.calculation_map.keys()))
        return df

    def validate(self, df: pd.DataFrame, return_calculated_columns: bool = True) -> pd.DataFrame:
        """Validate a DataFrame based on the schema."""
        df = self.schema.validate(df)
        if not return_calculated_columns:
            return df.drop(columns=list(self.calculation_map.keys()))
        return df


def load_schema_from_yaml(yaml_path: Path) -> DataFrameSchema:
    """Load a DataFrameSchema from a YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        schema_dict = yaml.safe_load(f)

    columns = {
        col_name: Column(**_deserialize_component_stats(col_stats))
        for col_name, col_stats in schema_dict["columns"].items()
    }

    return DataFrameSchema(
        columns=columns,
        checks=schema_dict.get("checks"),
        index=schema_dict.get("index"),
        dtype=schema_dict.get("dtype"),
        coerce=schema_dict.get("coerce", False),
        strict=schema_dict.get("strict", False),
        name=schema_dict.get("name", None),
        ordered=schema_dict.get("ordered", False),
        unique=schema_dict.get("unique", None),
        report_duplicates=schema_dict.get("report_duplicates", "all"),
        unique_column_names=schema_dict.get("unique_column_names", False),
        add_missing_columns=schema_dict.get("add_missing_columns", False),
        title=schema_dict.get("title", None),
        description=schema_dict.get("description", None),
    )


def _deserialize_component_stats(serialized_component_stats):
    dtype = serialized_component_stats.get("dtype")
    if dtype:
        dtype = pandas_engine.Engine.dtype(dtype)

    description = serialized_component_stats.get("description")
    title = serialized_component_stats.get("title")

    checks = serialized_component_stats.get("checks")
    if checks is not None:
        checks = [
            _deserialize_check_stats(
                getattr(Check, check_name), check_stats, dtype
            )
            for check_name, check_stats in checks.items()
        ]

    return {
        "title": title,
        "description": description,
        "dtype": dtype,
        "checks": checks,
        **{
            key: serialized_component_stats.get(key)
            for key in [
                "name",
                "nullable",
                "unique",
                "coerce",
                "required",
                "regex",
                "metadata"
            ]
            if key in serialized_component_stats
        },
    }