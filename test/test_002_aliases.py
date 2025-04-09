import pandas as pd
import pytest

@pytest.mark.parametrize("load_schema", ["aliases"], indirect=True)
def test_aliases(load_schema, processor):

    # test the expected key is in the supported list
    assert "aliases" in processor.supported_column_meta_keys

    df = pd.DataFrame({"pets": ['Tom', 'Jerry']})
    expected_df = pd.DataFrame({"my_pet_column": ['Tom', 'Jerry']})
    processor.schema = load_schema
    result_df = processor.apply_rename_from_alias(df)
    pd.testing.assert_frame_equal(result_df, expected_df)