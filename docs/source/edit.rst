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

When ``fred edit`` is started, the top-level sections of the metadata file are displayed as a numbered list. Select the section you want to edit by entering the corresponding number. FRED then steps through the keys within that section, showing the current value and allowing you to enter a new one.

The same dialog options as in :doc:`generate` are available:

- Press **Enter** to keep the current value unchanged.
- Type a new value to overwrite the current one.
- Enter ``!back`` to go back to the previous field.

Auto-generated fields (such as condition names and sample names) are recalculated automatically when the values they depend on are changed.
