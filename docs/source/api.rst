Python API
===========

In addition to the command-line interface, FRED can be used directly as a Python library. All functions are available through the ``FRED`` class in ``fred.metaTools``.

Initialization
---------------

.. code-block:: python

    from fred.metaTools import FRED

    fred = FRED(config="path/to/config.yaml")

The ``config`` argument accepts a path to a YAML config file. If the default config should be used, pass the path to ``fred/config/config.yaml`` inside the installed package:

.. code-block:: python

    import os
    from fred.metaTools import FRED

    default_config = os.path.join(os.path.dirname(fred.__file__), "config", "config.yaml")
    fred = FRED(config=default_config)

On initialization, FRED reads the config, clones or updates the whitelist repository, and loads the metadata structure.

Methods
--------

find
^^^^^

Search for metadata files matching a search string.

.. code-block:: python

    fred.find(
        search_path,       # path to directory to search in
        search,            # search string (same syntax as CLI -s)
        output,            # "print" or "json"
        output_filename,   # filename for json output (None = auto)
        skip_validation,   # bool: skip validation during search
    )

**Returns:** None (prints results or saves to file)

**Example:**

.. code-block:: python

    fred.find(
        search_path="/data/projects",
        search='organism_name:"Homo_sapiens"',
        output="print",
        output_filename=None,
        skip_validation=False,
    )

generate
^^^^^^^^^

Start an interactive dialog to create a new metadata file.

.. code-block:: python

    fred.generate(
        path,           # directory where the file is saved
        project_id,     # project ID string
        mandatory_only, # bool: only prompt mandatory fields
    )

validate
^^^^^^^^^

Validate a metadata file or all metadata files in a directory.

.. code-block:: python

    errors, warnings = fred.validate(
        logical_validation, # bool: perform logical validation
        path,               # path to file or directory
        output,             # "print", "txt", "json", "yaml", or None (interactive)
        output_filename,    # filename for saved report (None = auto)
    )

**Returns:** ``(error_count, warning_count)`` as integers.

**Example:**

.. code-block:: python

    errors, warnings = fred.validate(
        logical_validation=True,
        path="/data/projects/dst123_metadata.yaml",
        output="print",
        output_filename=None,
    )
    if errors == 0:
        print("File is valid.")

edit
^^^^^

Start an interactive dialog to edit an existing metadata file.

.. code-block:: python

    fred.edit(
        path,           # path to the metadata YAML file
        mandatory_only, # bool: only show mandatory fields
    )

export
^^^^^^^

Export a metadata file to MAGE-TAB or GEO format.

.. code-block:: python

    fred.export(
        path,         # path to the metadata YAML file
        output_dir,   # output directory (None = output_path from config)
        filename,     # base filename (None = project ID)
        mapping_path, # path to custom mapping YAML (None = default)
        settings,     # comma-separated setting IDs to export, e.g. "exp1,exp2" (None = all)
        fmt,          # "mage-tab" (default) or "geo"
    )

**Example:**

.. code-block:: python

    # Export to MAGE-TAB
    fred.export(
        path="/data/projects/dst123_metadata.yaml",
        output_dir="/data/output",
        filename=None,
        mapping_path=None,
        settings=None,
        fmt="mage-tab",
    )

    # Export to GEO spreadsheet
    fred.export(
        path="/data/projects/dst123_metadata.yaml",
        output_dir="/data/output",
        filename=None,
        mapping_path=None,
        settings=None,
        fmt="geo",
    )

fetch_whitelists
^^^^^^^^^^^^^^^^^

Manually trigger an update of the whitelist repository. This is called automatically on initialization when ``update_whitelists`` is ``True`` in the config.

.. code-block:: python

    fred.fetch_whitelists()
