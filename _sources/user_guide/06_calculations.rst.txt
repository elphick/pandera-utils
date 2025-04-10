Calculations
============

Rather than storing redundant data, it may make sense to store only the essential data
and calculate the rest.  This can be done in the schema.

The calculation key is used to store a string that can be evaluated by pandas, using the `eval` function.
This can be used to calculate a new column based on the values of other columns.

In this example, the moisture content of a sample is calculated from the wet and dry mass.

.. literalinclude:: ../../../assets/calculation_schema.yaml
   :language: yaml

For more information see the `pandas documentation <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.eval.html>`_.