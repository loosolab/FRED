File Validation
================

FRED includes a function to validate metadata files against the defined structure and whitelists.

Validation levels
------------------

FRED performs validation on three levels:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - **Structural**
     - Checks that all mandatory keys are present and that no unknown keys appear in the file.
   * - **Whitelist**
     - Checks that values for keys with a whitelist are valid entries from that whitelist.
   * - **Logical**
     - Checks semantic consistency, for example that all conditions are built from the declared experimental factors and that sample names match the expected pattern.

Function Call
--------------

The validate function of FRED is called via

.. code-block:: bash

    fred validate

with the following arguments:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-p, \-\-path
     - The path to the metadata file or directory to be validated. If a directory is given, all metadata files found within it are validated.

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
   * - \-l, \-\-skip_logic
     - Skip the logical validation level. Structural and whitelist validation are still performed.
     - flag; if stated, logical validation is skipped
   * - \-o, \-\-output
     - Define how the validation report should be displayed or saved.
     - ``print`` (default), ``json``, ``txt``, ``yaml``
   * - \-f, \-\-filename
     - Filename for the saved report. Only relevant when ``-o`` is set to ``json``, ``txt``, or ``yaml``.
     - path to output file
   * - \-c, \-\-config
     - Path to a config file. If not stated, the default config is used.
     - path to a YAML file

Validation report
------------------

After validation, FRED prints a summary of the results. For each validated file, the report lists:

- **Missing mandatory keys** — keys required by the structure that are absent from the file.
- **Invalid keys** — keys present in the file that are not defined in the structure.
- **Invalid entries** — values that do not conform to the expected format (e.g. wrong date format, wrong data type).
- **Invalid values** — values that are not in the corresponding whitelist.
- **Logical warnings** — semantic issues such as conditions that do not match the declared experimental factors.

When validating a directory, a final summary shows the total number of valid and invalid files.
