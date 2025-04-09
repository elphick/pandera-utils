import pytest
from pandera import DataFrameSchema, Column
from pandera.typing import String

from elphick.pandera_utils import DataFrameMetaProcessor


def test_check_schema_duplicate_aliases():
    schema = DataFrameSchema({
        "col1": Column(String, metadata={"pandera_utils": {"aliases": ["alias1"]}}),
        "col2": Column(String, metadata={"pandera_utils": {"aliases": ["alias1"]}}),
    })
    processor = DataFrameMetaProcessor(schema)
    with pytest.raises(ValueError, match="Duplicate aliases found: {'alias1'}"):
        processor.check_schema()


def test_check_schema_alias_keys_not_strings():
    schema = DataFrameSchema({
        "col1": Column(String, metadata={"pandera_utils": {"aliases": [123]}}),
    })
    processor = DataFrameMetaProcessor(schema)
    with pytest.raises(TypeError, match="Alias '123' in column 'col1' is not a string. All alias keys must be strings."):
        processor.check_schema()


def test_check_schema_inconsistent_category_map_keys():
    schema = DataFrameSchema({
        "col1": Column(String, metadata={"pandera_utils": {"category": {"key1": {}, "key2": {}}}}),
        "col2": Column(String, metadata={"pandera_utils": {"category": {"key1": {}}}}),
    })
    processor = DataFrameMetaProcessor(schema)
    with pytest.raises(ValueError, match="Inconsistent category map keys in column 'col2'."):
        processor.check_schema()