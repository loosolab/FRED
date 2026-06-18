File Editing
=============

FRED includes a function to interactively edit an existing metadata file. The editing dialog reuses the same interface as :doc:`generate`, so the workflow will feel familiar.

Function Call
--------------

The edit function of FRED is called via

.. code-block:: bash

    fred edit

with the following arguments:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-p, \-\-path
     - The path to the metadata YAML file to be edited.

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
   * - \-mo, \-\-mandatory_only
     - If stated, only mandatory keys are shown for editing.
     - flag
   * - \-c, \-\-config
     - Path to a config file. If not stated, the default config is used.
     - path to a YAML file

Editing workflow
-----------------

When ``fred edit`` is started, the top-level sections of the metadata file are displayed as a numbered list. You can select one or more sections to edit (comma-separated). FRED then steps through the editable keys within each selected section.

The behavior depends on the type of field:

- **List fields** — The existing entries are displayed as numbered options. You can choose to edit a specific entry, remove an entry, or add a new one.
- **Simple fields** — A new value is prompted directly.
- Enter ``!back`` to go back to the previous field.

Fields marked as auto-generated (e.g. IDs, setting IDs, sample names) are skipped and cannot be modified directly.
