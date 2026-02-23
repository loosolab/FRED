File Generation
=================

With FRED, you can create metadata files in YAML format. The information for the metadata is entered using interactive dialogs.


Function Call
----------------

The generate function of FRED is called via

.. code-block:: bash
    
    fred generate

with the following arguments:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-p, \-\-path
     - The path to the directory where the generated metadata YAML is to be stored.
   * - \-id, \-\-id
     - The ID of the project.
   * - \-c, \-\-config 
     - The path to a config file. If not stated, the default config is used.

The generate function has a mode in which only mandatory keys are requested in order to speed up metadata entry. The mandatory-only mode can be activated with the following argument:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-mo, \-\-mandatory_only
     - If stated, the mandatory-only mode is activated.

To show the correct usage of the function, as well as all possible arguments in a help message, the function also be called with the parameter:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-h, \-\-help
     - Show a help message.


Metadata Input 
-----------------

Dialog Options
^^^^^^^^^^^^^^^^^

.. list-table::
   :width: 100%

   * - Text input
     - Selections
     - Autofill
   * - 
       .. thumbnail:: ../images/text_input.gif
          :width: 100%
    
     - TBA
     - TBA
