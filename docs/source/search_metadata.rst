File Searching
=================

FRED includes a function to find metadata files using a search string over a specified path.

Function Call
----------------


The find function of FRED is called via

.. code-block:: bash
    
    fred find

with the following arguments:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-p, \-\-path
     - The path to the directory that should be searched.
   * - \-s, \-\-search
     - The search string.

To show the correct usage of the function, as well as all possible arguments in a help message, the function also be called with the parameter:

.. list-table::
   :width: 100%
   :widths: 25 75

   * - \-h, \-\-help
     - Show a help message.

Defining a search string
----------------------------

The search string contains the values to be searched for which must be enclosed in double quotes. Multiple search values can be linked via **and**\ , **or** and **not**\ .
The conjunction **and** corresponds to a logical and, whereas the conjunction **or** corresponds to a logical or. By prepending a **not** to the specified value, a search is performed for all values that do not correspond to it.

**Examples:**

.. list-table::
   :width: 100%
   :widths: 25 75

   * -
        .. code-block:: bash

            -s "Homo_sapiens"

     - search for files that contain 'Homo_sapiens'
   * -
        .. code-block:: bash

            -s 'not "Homo_sapiens"'

     - search for files that do not contain 'Homo_sapiens'
   * -
        .. code-block:: bash

            -s '"Homo_sapiens" and "lung"'

     - search for files that contain 'Homo_sapiens' and 'lung'
   * -
        .. code-block:: bash

            -s '"Homo_sapiens" or "Mus_musculus"'

     - search for files that contain 'Homo_sapiens' or 'Mus_musculus'


Increase accuracy
^^^^^^^^^^^^^^^^^^^^

Specifying a simple value, such as 'human' in the search string will cause all fields within the yaml file to be searched.
If only a specific field should contain the searched value, a key can be specified to limit the search. The key is placed in front of the value and separated from the value with a colon. 

e.g.

``-s 'organism_name:"Homo_sapiens"'`` searches for files that contain 'Homo_sapiens' as organism name

Multiple keys can also be chained together with colons to narrow the search even further. However, it should be noted that the order of the keys must match the indentations within the underlying yaml structure.

**Example:**

The following yaml shows the structure of the keys for the project part.

.. code-block:: yaml
    project:
        project_name:
        date:
        owner:
            name:
            ldap_name:
            department:
            email:
            address:
            telephone:
        nerd:
            name:
            ldap_name:
            department:
            email:
            address:
            telephone:
        description:
        further_description:
        graphical_abstract:

.. list-table::
   :width: 100%
   :widths: 25 75

   * -
        .. code-block:: bash

            -s "Mustermann, Max"

     - search for 'Mustermann, Max' in all fields
   * -
        .. code-block:: bash

            -s 'project:owner:name:"Mustermann, Max"'

     - search for 'Mustermann, Max' only as the name of the owner

Using brackets
^^^^^^^^^^^^^^^^^^

Round brackets in the search string are used to specify the order of evaluation.

If search strings are concatenated with 'and' and 'or', 'and' is normally evaluated first.

e.g. 

``gender:"female" or gender:"male" and organism_name:"Homo_sapiens"``

is evaluated as

``gender:"female" or (gender:"male" and organism_name:"Homo_sapiens")``

To explicitly specify the order in which the individual search terms are to be evaluated, round brackets can be integrated in the search string. The content within the round brackets is then evaluated first. It is also possible to nest several round brackets, in which case they are evaluated from the inside out.

