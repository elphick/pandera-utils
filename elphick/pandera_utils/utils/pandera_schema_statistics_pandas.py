"""
NOTE: https://github.com/unionai-oss/pandera/issues/1301

This code that is duplicated from https://github.com/unionai-oss/pandera/blob/main/pandera/io/pandas_io.py,
is a temporary solution to solve persistence of column metadata.
One a fix is implemented in pandera, this coe can be removed.
"""

from pandera.schema_statistics import parse_checks, get_index_schema_statistics


def get_dataframe_schema_statistics(dataframe_schema):
    """Get statistical properties from dataframe schema."""
    statistics = {
        "columns": {
            col_name: {
                "dtype": column.dtype,
                "nullable": column.nullable,
                "coerce": column.coerce,
                "required": column.required,
                "regex": column.regex,
                "checks": parse_checks(column.checks),
                "unique": column.unique,
                "description": column.description,
                "title": column.title,
                "metadata": column.metadata,
            }
            for col_name, column in dataframe_schema.columns.items()
        },
        "checks": parse_checks(dataframe_schema.checks),
        "index": (
            None
            if dataframe_schema.index is None
            else get_index_schema_statistics(dataframe_schema.index)
        ),
        "coerce": dataframe_schema.coerce,
    }
    return statistics


def _get_series_base_schema_statistics(series_schema_base):
    return {
        "dtype": series_schema_base.dtype,
        "nullable": series_schema_base.nullable,
        "checks": parse_checks(series_schema_base.checks),
        "coerce": series_schema_base.coerce,
        "name": series_schema_base.name,
        "unique": series_schema_base.unique,
        "title": series_schema_base.title,
        "description": series_schema_base.description,
        "metadata": series_schema_base.metadata,
    }
