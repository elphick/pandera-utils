from importlib import metadata

from .pandera_utils import DataFrameMetaProcessor, load_schema_from_yaml

try:
    __version__ = metadata.version('pandera_utils')
except metadata.PackageNotFoundError:
    # Package is not installed
    pass