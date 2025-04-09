import copy

import pandas as pd
from pandera import DataFrameSchema

from elphick.pandera_utils import DataFrameMetaProcessor


def test_load_schema(schema):
    assert isinstance(schema, DataFrameSchema)


def test_validate_schema(processor):
    processor.check_schema()


def test_unit_of_measure_map(processor):
    expected = {'my_length_column': 'm', 'wet_mass': 'kg', 'dry_mass': 'kg', 'moisture': '%'}
    assert processor.unit_of_measure_map == expected


def test_alias_map(processor):
    expected = {'my_pet_column': ['pets', 'my_pets']}
    assert processor.alias_map == expected


def test_calculation_map(processor):
    expected = {'moisture': '(wet_mass - dry_mass) / dry_mass * 100'}
    assert processor.calculation_map == expected


def test_decimals_map(processor):
    expected = {'my_float_column': 2}
    assert processor.decimals_map == expected


def test_missing_sentinels_map(processor):
    expected = {'my_nullable_int_column': [-1, -9]}
    assert processor.missing_sentinels_map == expected


def test_category_maps(processor):
    expected = {'my_color_column': {'description': {'dtype': 'category',
                                                    'map': {'B': 'The color blue',
                                                            'G': 'The color green',
                                                            'R': 'The color red'}},
                                    'label': {'dtype': 'category',
                                              'map': {'B': 'Blue', 'G': 'Green', 'R': 'Red'}},
                                    'wavelength': {'dtype': 'int',
                                                   'map': {'B': 435, 'G': 546, 'R': 700}}}}
    assert processor.category_maps == expected


def test_category_ordered_map(processor):
    expected = {'my_color_column': False}
    assert processor.category_ordered_map == expected


def test_apply_rename_from_alias(processor):
    df = pd.DataFrame({"my_pets": ['Tom', 'Jerry']})
    expected_df = pd.DataFrame({"my_pet_column": ['Tom', 'Jerry']})
    result_df = processor.apply_rename_from_alias(df)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_apply_calculations(processor):
    df = pd.DataFrame({"wet_mass": [100, 110], "dry_mass": [90.0, 100]})
    expected_df = pd.DataFrame({"wet_mass": [100, 110], "dry_mass": [90.0, 100.0], "moisture": [11.111111, 10.0]})
    result_df = processor.apply_calculations(df)
    pd.testing.assert_frame_equal(result_df, expected_df, atol=1.0e-04)


def test_apply_rounding(processor):
    df = pd.DataFrame({"my_float_column": [3.123, 4.567], 'my_unmanaged_float': [5.767447, 6.56765]})
    expected_df = pd.DataFrame({"my_float_column": [3.12, 4.57], 'my_unmanaged_float': [5.767447, 6.56765]})
    result_df = processor.apply_rounding(df)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_apply_missing_sentinels(processor):
    df = pd.DataFrame({"my_nullable_int_column": [1, 2, 3, -9, -100]})
    expected_df = pd.DataFrame({"my_nullable_int_column": [1, 2, 3, pd.NA, -100]}).astype(
        {'my_nullable_int_column': 'Int8'})
    result_df = processor.apply_missing_sentinels(df)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_apply_category_maps(processor):
    df = pd.DataFrame({"my_color_column": pd.Categorical(["B", "R", "G"], categories=['R', 'G', 'B'])})
    expected_df = pd.DataFrame({"my_color_column": pd.Categorical(["B", "R", "G"], categories=['R', 'G', 'B']),
                                "my_color_column_label": pd.Categorical(["Blue", "Red", "Green"],
                                                                        categories=["Red", "Green", "Blue"]),
                                "my_color_column_description": pd.Categorical([
                                    "The color blue", "The color red", "The color green"],
                                    categories=["The color red", "The color green", "The color blue"]),
                                "my_color_column_wavelength": [435, 700, 546]})
    result_df = processor.apply_category_maps(df)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_preprocess(processor):
    df = pd.DataFrame({"my_pets": ['Tom', 'Jerry'], "my_float_column": [3.123, 4.567]})
    expected_df = pd.DataFrame({"my_pet_column": ['Tom', 'Jerry'], "my_float_column": [3.12, 4.57]})
    # modify the schema to enable the test to pass
    processor: DataFrameMetaProcessor = copy.deepcopy(processor)
    del processor.schema.columns['my_color_column']
    del processor.schema.columns['moisture']
    result_df = processor.preprocess(df)
    pd.testing.assert_frame_equal(result_df, expected_df)


def test_validate(processor):
    processor: DataFrameMetaProcessor
    # set the dataframe level keys to enable column sorting
    # this is a workaround for the test to pass
    processor.schema.metadata = {'order_columns': True}
    processor.schema.coerce = True

    df1 = pd.DataFrame({'my_length_column': [1.0, 2.0]})
    df2 = pd.DataFrame({"my_pets": ['Tom', 'Jerry']})
    df3 = pd.DataFrame({"my_nullable_int_column": [100, -9]})
    df4 = pd.DataFrame({"wet_mass": [100, 110], "dry_mass": [90.0, 100]})
    df5 = pd.DataFrame({"my_float_column": [3.123, 4.567], 'my_unmanaged_float': [5.767447, 6.56765]})
    df6 = pd.DataFrame({"my_color_column": pd.Categorical(["B", "R"], categories=['R', 'G', 'B'])})

    df = pd.concat([df1, df2, df3, df4, df5, df6], axis=1)
    pp_df = processor.preprocess(df)
    result_df = processor.validate(pp_df)

    assert pp_df.columns.equals(result_df.columns)

    # manually modify the columns (mimic the processor) to allow the assertion to pass
    pp_df['my_float_column'] = pp_df['my_float_column'].astype('float32')
    pp_df['wet_mass'] = pp_df['wet_mass'].astype('float32')
    pp_df['dry_mass'] = pp_df['dry_mass'].astype('float32')
    pp_df['moisture'] = pp_df['moisture'].astype('float32')

    pd.testing.assert_frame_equal(result_df, pp_df)
