User Guide
==========

The purpose of this guide is to walk the user through how-to use the package.
It is complemented by the examples.

The ``metadata`` property exists at the ``dataframe`` level and the ``column`` level of
the pandera ``DataFrameSchema``.

The ``metadata`` property is a dictionary that can be used to
store any additional information about the schema.  This package leverages specified keys in the
``metadata`` property to add additional functionality to the schema.

The yaml format is useful for pre-defining the schema, with the general pattern to support ``pandera-utils`` being:

.. code-block:: yaml

   schema_type: dataframe
   metadata:
     pandera_utils:
       <key>: <value>
       <key>: <value>
       ...
   columns:
     <column_name>:
       metadata:
         pandera_utils:
           <key>: <value>
           <key>: <value>
           ...

.. toctree::
   :maxdepth: 2
   :hidden:
   :glob:

   user_guide/*