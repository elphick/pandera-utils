Aliases
=======

While mapping columns is not difficult, the schema provides a nice platform to manage renames by specifying
aliases for a column.

If duplicate aliases are provided in the same schema file, the file will fail the schema check, prior to validation.
Kind of obvious, since we must avoid ambiguity.

.. literalinclude:: ../../../assets/aliases_schema.yaml
   :language: yaml