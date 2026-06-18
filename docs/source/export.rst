Metadata Export
================

FRED can export metadata files to standardized formats used by public data repositories. Two formats are currently supported:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - **MAGE-TAB**
     - Produces an IDF (Investigation Description Format) file and an SDRF (Sample and Data Relationship Format) file. Used for submissions to `ArrayExpress <https://www.ebi.ac.uk/biostudies/arrayexpress>`_.
   * - **GEO**
     - Produces a GEO metadata spreadsheet (``.xlsx``). Used for submissions to `NCBI GEO <https://www.ncbi.nlm.nih.gov/geo/>`_.

Function Call
--------------

The export function of FRED is called via

.. code-block:: bash

    fred export

with the following arguments:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-p, \-\-path
     - The path to the metadata YAML file to export.

To show the correct usage of the function, as well as all possible arguments in a help message, the function can also be called with the parameter:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-h, \-\-help
     - Show a help message.

Optional arguments
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :width: 100%
   :widths: 20 30 30
   :header-rows: 1

   * - Argument
     - Description
     - Value
   * - \-\-format
     - Export format.
     - ``mage-tab`` (default) or ``geo``
   * - \-o, \-\-output_dir
     - Output directory for the generated files. Defaults to ``output_path`` from the config.
     - path to directory
   * - \-f, \-\-filename
     - Base filename for the output files. Defaults to the project ID from the metadata file.
     - string
   * - \-m, \-\-mapping
     - Path to a custom mapping YAML file. If not stated, the default mapping for the selected format is used (``fred/config/mage_tab_mapping.yaml`` or ``fred/config/geo_metadata_mapping.yaml``).
     - path to a YAML file
   * - \-s, \-\-settings
     - Comma-separated list of experimental setting IDs to export. If not stated, all settings are exported.
     - e.g. ``exp1,exp3``
   * - \-c, \-\-config
     - Path to a config file. If not stated, the default config is used.
     - path to a YAML file

Examples
---------

Export a metadata file to MAGE-TAB (default):

.. code-block:: bash

    fred export -p /path/to/my_metadata.yaml

Export to GEO format, saving to a specific directory:

.. code-block:: bash

    fred export -p /path/to/my_metadata.yaml --format geo -o /path/to/output/

Export only the first experimental setting to MAGE-TAB:

.. code-block:: bash

    fred export -p /path/to/my_metadata.yaml -s exp1
