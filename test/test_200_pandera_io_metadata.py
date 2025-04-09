import json

import pandera as pa
import pytest

from elphick.pandera_utils.utils.pandera_io_pandas_io import to_json, from_json


#  NOTE: https://github.com/unionai-oss/pandera/issues/1301

@pytest.mark.skip(reason="Skipping due to a known bug in pandera")
def test_roundtrip_metadata():
    schema = pa.DataFrameSchema(
        columns={
            "col": pa.Column(int, metadata={"key": "value"}),
        },
    )
    # out = schema.to_json()
    out = to_json(schema)
    print(json.dumps(json.loads(out), indent=4))
    # assert schema == pa.DataFrameSchema.from_json(out)
    assert schema == from_json(out)
