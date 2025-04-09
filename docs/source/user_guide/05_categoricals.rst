Categoricals
============

``Categoricals`` enable compact storage of objects (strings).  Sure they come with a
learning curve, but they can be very useful.

A categorical column is essentially a map of an integer (called ``cat_codes``) to each string, which enables repeated rows of strings
to be stored with less memory.  The user sees the string they expect, but the memory overhead is reduced.

The pandera_utils package allows you to add additional maps to each category.  Typical use cases include
adding a label or description.

.. literalinclude:: ../../../assets/category_schema.yaml
   :language: yaml

The ``isin`` check is used to define the categories that are allowed in the column, in the case that
the ``add_all_categories`` key is not set to false.  If the key is set to false, only categories present in the
loaded data will define the allowable categories.

For more information see the `pandas documentation <https://pandas.pydata.org/pandas-docs/stable/user_guide/categorical.html>`_.