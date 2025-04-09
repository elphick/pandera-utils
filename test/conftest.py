# conftest.py
import pytest
import pandas as pd
from pathlib import Path
from elphick.pandera_utils.pandera_utils import load_schema_from_yaml, DataFrameMetaProcessor, merge_schemas


@pytest.fixture(scope="module")
def schema():
    asset_path: Path = Path(__file__).resolve().parents[1] / 'assets'
    schema_keys: list[str] = ['unit_of_measure', 'aliases', 'decimals', 'missing_sentinels', 'category', 'calculation']

    schema_list = [load_schema_from_yaml(asset_path / f"{sk}_schema.yaml") for sk in schema_keys]
    return merge_schemas(schema_list)


@pytest.fixture(scope="module")
def processor(schema):
    return DataFrameMetaProcessor(schema)


@pytest.fixture(scope="module")
def processor_category(schema_category):
    return DataFrameMetaProcessor(schema_category)


@pytest.fixture(scope="module")
def dataframe():
    return pd.DataFrame({"col1": [1, 2], "column2": [3.123, 4.567]})


@pytest.fixture(scope="module")
def dataframe_category():
    return pd.DataFrame({
        "int1": [1, 2],
        "cat1": ["A", "B"],
        "float1": [3.12, 4.56],
        "cat2": ["R", "G"]
    })


@pytest.fixture
def load_schema(request):
    feature = request.param
    yaml_path = Path(__file__).resolve().parents[1] / 'assets' / f"{feature}_schema.yaml"
    return load_schema_from_yaml(yaml_path)
