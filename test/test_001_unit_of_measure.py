import pandas as pd
import pytest

@pytest.mark.parametrize("load_schema", ["unit_of_measure"], indirect=True)
def test_unit_of_measure(load_schema, processor):

    # test the expected key is in the supported list
    assert "unit_of_measure" in processor.supported_column_meta_keys

    df = pd.DataFrame({"column1": [3, 4], "column2": [4.123, 6.567]})
    expected_df = df
    processor.schema = load_schema
    result_df = processor.apply_rounding(df)
    pd.testing.assert_frame_equal(result_df, expected_df)