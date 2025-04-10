Order Columns
=============

At the ``dataframe`` level, the metadata key can be used to extend the base pandera functionality by ordering
the columns to match the order defined in the schema.

This is useful when you are using the schema to define the order of the columns in a dataframe.

.. code-block::  yaml

   schema_type: dataframe
   metadata:
     pandera_utils:
       order_columns: true

Columns in the schema will be ordered in the dataframe to match the order defined in the schema.  Additional columns
in the dataframe will be placed at the end of the dataframe in the order they appear in the dataframe.

Consider the existing pandera `DataFrameSchema
<https://pandera.readthedocs.io/en/stable/reference/generated/pandera.api.polars.container.DataFrameSchema.html
#pandera-api-polars-container-dataframeschema>`_ functionality, particularly the ``strict`` and ``ordered`` properties
and how they may interact with the ``order_columns`` property.  Typically the metaprocessor
`DataFrameMetaProcessor <../api/_autosummary/elphick.pandera_utils.pandera_utils.DataFrameMetaProcessor.html>`_ will be executed first,
followed by the standard pandera validation.DataFrameMetaProcessor