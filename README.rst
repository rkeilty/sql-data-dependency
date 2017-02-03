SQL Data Dependency Tool
========================

The SQL Data Dependency Tool (``sqldd``) is a tookit used for analyzing dependencies between rows in a database.  Given a table and a primary key, it recursively analyzes foreign keys to generate a map of all downstream tables and foreign keys the initial "root row" depends on.

Installation
============

The ``sqldd`` module is `published on the Python Package
Index <https://pypi.python.org/pypi/sqldd>`__, so you can
install it using ``pip`` or ``easy_install``.

::

    pip install sqldd

Or:

::

    easy_install sqldd

It installs a ``sqldd`` module in the path for simple shell usage.

Usage
=====

The most common usage of the tool is from the shell with ``sqldd``.

For example, to find dependencies of row 53 in table A:
::

    $: sqldd A 53
       {u'A': [53],
        u'D': [1, 2, 20],
        u'M': [48]}

This indicates that in the complete dependency tree for that row, tables ``D`` and ``M`` have rows that matter to foreign keys.  This may not be a direct child dependency of ``A``, but possibly a sub-dependency (``A:53 --> D:1 --> M:48``)

Multiple rows
-------------
For more complex analysis, where one may want to look at multiple tables/rows, a JSON file can be specified with table names as keys, and values are arrays of primary keys.

::

    {
        "A": [53],
        "another_table": [1, 4, 10],
        "one_more_table": ["string_pk_1", "string_pk_2"]
    }
    
Now invoking will give more output:

::

    $: sqldd --json input.json
       {u'A': [53],
        u'another_table': [1, 4, 10, 22, 28],
        u'D': [1, 2, 20],
        u'M': [48],
        u'P': [800, 908],
        u'one_more_table': ["string_pk_1", "string_pk_2", "string_pk_4444"]}

Options
-------
::
    
    usage: sqldd [-h] [--json JSON_FILE] [--server SERVER] [--port PORT]
                 --database DATABASE [--username USERNAME]
                 [--password PASSWORD] [--mysqldump] [--mysqldump_gzip]
                 [--mysqldump_table_defs]
                 [table] [primary_key]

    SQL Data Dependency Tool
    
    One of either ([table][primary_key]) or [--json] is required.

    positional arguments:
      table                 Table to analyze
      primary_key           Primary key for row in table to analyze

    optional arguments:
      -h, --help            show this help message and exit
      --json JSON_FILE      File containing tables and rows to analyze
      --server SERVER       Database server
      --port PORT           Database port
      --database DATABASE   Database name
      --username USERNAME   Database username
      --password PASSWORD   Database password
      --mysqldump           Generate a mysqldump file of all dependencies
      --mysqldump_gzip      GZip the mysqldump output
      --mysqldump_table_defs
                            Dump _all_ table defs, even those without
                            dependencies. Useful for constructing skeleton DBs.

Todo
====
- Allow for traversing *up* from root rows, rather than just downstream dependencies.
- Compound primary keys are not supported.
- Restricted to MySQL, expand connection strings to allow *any* SQL compatible DB access.

License
=======

``sqldd`` is licensed under the terms of the 3-clause BSD license.

Contributing
============

All contributions are welcome, including but not limited to:

-  Documentation fixes / updates
-  New features (requests as well as implementations)
-  Bug fixes (see issues list)

If you encounter any errors in the code, please file an issue on github:
https://github.com/rkeilty/sql-data-dependency/issues.

Author
======

-  Author: Rick Keilty
-  Email: rkeilty@gmail.com
-  Repository: http://github.com/rkeilty/sql-data-dependency

Version
=======

-  Version: 0.9.2
-  Release Date: 2017-02-03

Revision History
================

Version 0.9.2
-------------

-  Release Date: 2017-02-03
-  Changes:

   -  Allow for older SQLAlchemy usage

Version 0.9.1
-------------

-  Release Date: 2017-01-28
-  Changes:

   -  Fix for mysqldump command check
   -  Documentation updates

Version 0.9.0
-------------

-  Release Date: 2017-01-27
-  Changes:

   -  Initial release
