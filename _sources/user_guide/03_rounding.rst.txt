Rounding
========

Trailing decimal for floats can be problematic when comparing values.  While there are nice functions in pandas
and numpy to manage this, comparison is not the only problem.

More decimal places can imply more precision of the measurement than is actually present.  This can be misleading.
We may choose to round to a specific number of decimals to help infer measurement precision.

.. literalinclude:: ../../../assets/decimals_schema.yaml
   :language: yaml

For more information see the `pandas documentation <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.round.html>`_.