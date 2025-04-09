import pandas as pd
import pytest


@pytest.mark.parametrize("load_schema", ["decimals"], indirect=True)
def test_decimals(load_schema, processor):

    # test the expected key is in the supported list
    assert "decimals" in processor.supported_column_meta_keys

    df = pd.DataFrame({"my_float_column": [3.123, 4.567], "column2": [4.123, 6.567]})
    expected_df = pd.DataFrame({"my_float_column": [3.12, 4.57], "column2": [4.123, 6.567]})
    processor.schema = load_schema
    result_df = processor.apply_rounding(df)
    pd.testing.assert_frame_equal(result_df, expected_df)