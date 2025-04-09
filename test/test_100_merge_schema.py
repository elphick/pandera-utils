from pathlib import Path

import pytest

from elphick.pandera_utils import load_schema_from_yaml
from elphick.pandera_utils.pandera_utils import merge_schemas
from elphick.pandera_utils.utils.pandera_io_pandas_io import to_yaml

asset_path: Path = Path(__file__).parents[1] / "assets"


def test_merge_schema():
    """Test merging schemas with different metadata."""

    schema_keys: list[str] = ['unit_of_measure', 'aliases', 'decimals', 'missing_sentinels', 'category', 'calculation']

    schema_list = [load_schema_from_yaml(asset_path / f"{sk}_schema.yaml") for sk in schema_keys]
    merged_schema = merge_schemas(schema_list)

    # Check that the merged schema has the expected columns
    expected_columns = ['my_length_column', 'my_pet_column', 'my_float_column', 'my_nullable_int_column',
                        'my_color_column', 'wet_mass', 'dry_mass', 'moisture']
    assert set(merged_schema.columns.keys()) == set(expected_columns)

    # Check that the merged schema has the expected metadata
    assert merged_schema.columns['my_length_column'].metadata['pandera_utils']['unit_of_measure'] == 'm'
    assert merged_schema.columns['my_pet_column'].metadata['pandera_utils']['aliases'] == ['pets', 'my_pets']
    assert merged_schema.columns['my_float_column'].metadata['pandera_utils']['decimals'] == 2
    assert merged_schema.columns['my_nullable_int_column'].metadata['pandera_utils']['missing_sentinels'] == [-1, -9]
    assert merged_schema.columns['my_color_column'].metadata['pandera_utils']['category'] == {
        'add_all_categories': True,
        'ordered': False,
        'label': {
            'map': {'R': 'Red', 'G': 'Green', 'B': 'Blue'},
            'dtype': 'category'
        },
        'description': {
            'map': {'R': 'The color red', 'G': 'The color green', 'B': 'The color blue'},
            'dtype': 'category'
        },
        'wavelength': {
            'map': {'R': 700, 'G': 546, 'B': 435},
            'dtype': 'int'
        }}
    assert merged_schema.columns['moisture'].metadata['pandera_utils'][
               'calculation'] == '(wet_mass - dry_mass) / dry_mass * 100'
