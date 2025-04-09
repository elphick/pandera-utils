import pandas as pd
import pytest


@pytest.mark.parametrize("load_schema", ["missing_sentinels"], indirect=True)
def test_missing_values(load_schema, processor):
    # test the expected key is in the supported list
    assert "missing_sentinels" in processor.supported_column_meta_keys

    df = pd.DataFrame({"my_nullable_int_column": [1, 2, 3, -9, -100]})
    expected_df = pd.DataFrame({"my_nullable_int_column": [1, 2, 3, pd.NA, -100]}).astype({'my_nullable_int_column': 'Int8'})
    processor.schema = load_schema
    result_df = processor.validate(df)
    # Expect an assertion error if the result_df is not equal to expected_df

    with pytest.raises(AssertionError, match='my_nullable_int_column.+NA mask are different'):
        pd.testing.assert_frame_equal(result_df, expected_df)