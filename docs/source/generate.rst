File Generation
=================

.. |fig1| figure:: ../images/FRED_generate.png
    :align: right
    :width: 50%


|fig1| When publishing scientific studies, it is important to make all data and metadata available to promote scientific discovery and innovation. **FRED** allows users to create metadata files in a hierarchical structured YAML file using interactive dialogs.
The metadata is divided into three parts:


.. list-table::
   :width: 100%
   :widths: 25 75

   * - project
     - General information about the project like description or owner.
   * - experimental setting
     - Experimental Design information containing investigated conditions and their respective samples.
   * - technical details
     - Technical information about the project like sequencing technique or analysis runs.


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

   * - **Text input:**
       Free text entry consisting of words, numbers, or dates.
     - **Selections:**
     - **Autofill:**
   * - 
       .. thumbnail:: ../images/text_input.gif
          :width: 100%
    
     - TBA
     - TBA

Summary 
^^^^^^^^^^^^^^

After finishing a section of the metadata, a summary is displayed for checking if everything is correct. 
For the **project** and **technical details** section, the summary is displayed in YAML formatting. 
For the **experimental setting** section a plot is created. 

Experimental Factors, Conditions and Samples
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Select Experimental Factors
""""""""""""""""""""""""""""""""

Experimental Factors are used to create the conditions, so it is important to state all information that you actively compared between samples. 
Additional information that are not used to generate the conditions can be entered later per sample.
The following video explains how to differentiate experimental factors from additional information in more detail:

..  youtube:: 7SAsh-0FeR4
   :align: center
   :width: 100%

Combine Conditions
""""""""""""""""""""""

Add Samples
""""""""""""""""


Replicates
""""""""""""""""""

.. list-table::
   :width: 100%

   * - Biological Replicates
     - TBA
   * - Technical Replicates
     - TBA
   * - Number of Measurements
     - TBA
