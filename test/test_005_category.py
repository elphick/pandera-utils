import pandas as pd
import pytest


@pytest.mark.parametrize("load_schema", ["category"], indirect=True)
def test_category(load_schema, processor):
    # test the expected key is in the supported list
    assert "category" in processor.supported_column_meta_keys

    # Create a sample DataFrame
    df = pd.DataFrame({
        "my_color_column": pd.Categorical(["R", "G", "B", "R", "G", "B"])
    })

    # Load the schema from the file
    processor.schema = load_schema

    # Validate the DataFrame against the schema
    validated_df = processor.validate(df)

    # Check if the DataFrame is valid
    assert not validated_df.empty
    assert all(validated_df["my_color_column"].isin(["R", "G", "B"]))
    assert validated_df["my_color_column"].dtype.name == "category"

    # expand the output using processor.apply_category_maps method
    expanded_df = processor.apply_category_maps(validated_df)

    # Check if the expanded DataFrame is valid
    assert not expanded_df.empty
    assert all(expanded_df["my_color_column"].isin(["R", "G", "B"]))
    assert expanded_df["my_color_column"].dtype.name == "category"

