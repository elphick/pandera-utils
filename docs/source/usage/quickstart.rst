Quick Start Guide
=================

This page will describe the basic steps to use the package.

The package is designed to be used with pandera yaml schema files that
have been modified to include the ``metadata`` key for each of the column entries.

A good way to create a yaml schema from a pandas dataframe is to use the
`pandera.infer_schema <https://pandera.readthedocs.io/en/stable/schema_inference.html>`_ function.

You can add the following keys to the metadata key for each of your columns:

- unit_of_measure
- aliases
- decimals
- sentinel_values
- category
- calculation

..  code-block:: python

    import pandera-utils
    processor = DataFrameMetaProcessor(schema)

Pre-process the dataframe to manage aliases, rounding and perform calculations.

..  code-block:: python

    processed_df = processor.preprocess(dataframe)


Finally, you can validate the dataframe using the schema.

..  code-block:: python

    processor.validate(processed_df)

To disable the pre-processing on a particular column, you can set the
``coerce`` key to ``False`` in the schema.  While the core pandera package uses coerce to
coerce types, pander-utils uses the same key to disable pre-processing.