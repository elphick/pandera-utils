Nullable Integers
=================

Nullable integers solve the problem of missing data in integer columns. In
pandas, missing data is represented by ``np.nan``, which is a float. This
means that if you have a column with integers and missing data, pandas will
convert the integers to floats to accommodate the missing data.

This can be problematic if you want to maintain the integer data type.
The solution is to use nullable integers, which are available in pandas 1.0.0
and later. Nullable integers allow you to have missing data in integer columns
without converting the integers to floats.

To use nullable integers, you can specify the data type as ``Int64`` (note the upper case i) or similar.
This will allow you to have missing data in the column without converting the integers to floats.

The problem remains though that any "sentinel" values, such as negative
integers that are placeholders for missing data will remain.

By correctly configuring the schema for the column, you can specify the
value that should be treated as missing data.

.. literalinclude:: ../../../assets/missing_sentinels_schema.yaml
   :language: yaml

For more information see the `pandas documentation <https://pandas.pydata.org/pandas-docs/stable/user_guide/integer_na.html>`_.