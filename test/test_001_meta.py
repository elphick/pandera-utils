import numpy as np
import pytest
import pandas as pd
from pathlib import Path
from pandera import DataFrameSchema
from elphick.pandera_utils.pandera_utils import load_schema_from_yaml, DataFrameMetaProcessor


@pytest.fixture
def schema():
    yaml_path = Path("../assets/test_schema.yaml")
    return load_schema_from_yaml(yaml_path)


@pytest.fixture
def dataframe():
    return pd.DataFrame({
        "col1": [1, 2, 3],
        "column2": [0.546, 1.568, 2.578],
    })


def test_load_schema(schema):
    assert isinstance(schema, DataFrameSchema)


def test_preprocess_step_by_step(schema, dataframe):
    processor = DataFrameMetaProcessor(schema)

    # Step 1: Check if alias is applied correctly
    df_with_alias = processor.apply_rename_from_alias(dataframe)
    assert "column1" in df_with_alias.columns
    assert df_with_alias["column1"].equals(dataframe["col1"])

    # Step 2: Check if calculations are applied correctly
    df_with_calculations = processor.apply_calculations(df_with_alias)
    assert "column3" in df_with_calculations.columns
    assert df_with_calculations["column3"].equals(df_with_calculations["column1"] + df_with_calculations["column2"])

    # Step 3: Check if decimals are applied correctly
    df_with_decimals = processor.apply_rounding(df_with_calculations)
    assert df_with_decimals["column2"].dtype == "float64"
    assert df_with_decimals["column2"].apply(lambda x: x == round(x, 2)).all()


def test_preprocess(schema, dataframe):
    processor = DataFrameMetaProcessor(schema)
    processed_df = processor.preprocess(dataframe)
    assert "column1" in processed_df.columns
    np.testing.assert_almost_equal(processed_df["column3"].values, np.round((processed_df["column1"] + processed_df["column2"]).values, 2),6)

def test_validate(schema, dataframe):
    processor = DataFrameMetaProcessor(schema)
    processed_df = processor.preprocess(dataframe)
    validated_df = processor.validate(processed_df)
    assert not validated_df.empty
