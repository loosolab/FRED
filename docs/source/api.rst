Python API
===========

FRED provides a Python API for programmatic integration. All functions are located in ``fred.src.wi_functions``.

Initialization
---------------

The ``Webinterface`` class holds the program state (config, structure, whitelist path) and is passed as ``pgm_object`` to most API functions.

.. code-block:: python

    from fred.src.wi_functions import Webinterface

    wi = Webinterface(config="path/to/config.yaml")
    pgm_object = wi.to_dict()

On initialization, FRED reads the config, clones or updates the whitelist repository, and loads the metadata structure.

The ``pgm_object`` dictionary is passed as the first argument to most functions below.


Whitelist Management
---------------------

fetch_whitelists
^^^^^^^^^^^^^^^^^

Clone or update the whitelist repository. Called automatically on initialization.

.. code-block:: python

    from fred.src.wi_functions import fetch_whitelists

    fetch_whitelists(pgm_object)

get_whitelist_object
^^^^^^^^^^^^^^^^^^^^^

Load all whitelists and return them as a dictionary together with the current version.

.. code-block:: python

    from fred.src.wi_functions import get_whitelist_object

    whitelist_object = get_whitelist_object(pgm_object)
    # {"whitelists": {...}, "version": "..."}

get_single_whitelist
^^^^^^^^^^^^^^^^^^^^^

Fetch a single whitelist entry.

.. code-block:: python

    from fred.src.wi_functions import get_single_whitelist

    whitelist = get_single_whitelist(ob, read_in_whitelists)


Metadata Objects
-----------------

get_empty_wi_object
^^^^^^^^^^^^^^^^^^^^

Return an empty metadata object conforming to the current structure.

.. code-block:: python

    from fred.src.wi_functions import get_empty_wi_object, get_whitelist_object

    read_in_whitelists = get_whitelist_object(pgm_object)
    empty = get_empty_wi_object(pgm_object, read_in_whitelists)

is_empty
^^^^^^^^^

Check whether a metadata object contains no user-entered data.

.. code-block:: python

    from fred.src.wi_functions import is_empty

    result = is_empty(pgm_object, wi_object, read_in_whitelists)
    # {"empty": True/False, "object": <empty_object>}

validate_object
^^^^^^^^^^^^^^^^

Validate a metadata object against the structure and whitelists.

.. code-block:: python

    from fred.src.wi_functions import validate_object

    validated = validate_object(
        pgm_object,
        wi_object,
        read_in_whitelists,
        finish=False,   # set True to apply finish-time validation rules
    )

get_summary
^^^^^^^^^^^^

Generate an HTML summary of a metadata object.

.. code-block:: python

    from fred.src.wi_functions import get_summary

    html = get_summary(pgm_object, wi_object, read_in_whitelists)

save_object
^^^^^^^^^^^^

Serialize a metadata object and save it to a YAML file.

.. code-block:: python

    from fred.src.wi_functions import save_object

    obj, project_id = save_object(
        dictionary,    # metadata object as dict
        path,          # output directory
        filename,      # filename suffix (from config)
        edit_state,    # bool: True if editing an existing file
    )

save_filenames
^^^^^^^^^^^^^^^

Save a filename mapping string to the given path.

.. code-block:: python

    from fred.src.wi_functions import save_filenames

    save_filenames(file_str, path)

parse_object
^^^^^^^^^^^^^

Parse a metadata object into YAML-serializable form. In most cases ``get_summary`` is preferred.

.. code-block:: python

    from fred.src.wi_functions import parse_object

    result = parse_object(pgm_object, wi_object, read_in_whitelists, return_id=False)


Experimental Design
--------------------

get_factors
^^^^^^^^^^^^

Retrieve available experimental factors for a given organism.

.. code-block:: python

    from fred.src.wi_functions import get_factors

    factors = get_factors(pgm_object, organism, read_in_whitelists)

get_conditions
^^^^^^^^^^^^^^^

Generate condition combinations from selected factors and organism.

.. code-block:: python

    from fred.src.wi_functions import get_conditions

    conditions = get_conditions(pgm_object, factors, organism_name, read_in_whitelists)


Metadata File I/O
------------------

read_metadata
^^^^^^^^^^^^^^

Read a metadata YAML file and return it as a dictionary.

.. code-block:: python

    from fred.src.wi_functions import read_metadata

    metadata = read_metadata(path)

get_metadata
^^^^^^^^^^^^^

Read a metadata YAML file and return both the full metadata and a condensed search view.

.. code-block:: python

    from fred.src.wi_functions import get_metadata

    full_metadata, search_view = get_metadata(path)

get_metadata_search_view
^^^^^^^^^^^^^^^^^^^^^^^^^

Extract key fields from a metadata file for display in search results (project ID, owner, organisms, techniques, tissues, diseases, treatments).

.. code-block:: python

    from fred.src.wi_functions import get_metadata_search_view

    view = get_metadata_search_view(path)
    # {"id": "...", "project_name": "...", "owner": "...", "organisms": [...], ...}

add_nerd
^^^^^^^^^

Add a collaborator (nerd) to the nerd list of an existing metadata file. Returns ``False`` if a nerd with the same ``ldap_name`` already exists.

.. code-block:: python

    from fred.src.wi_functions import add_nerd

    added = add_nerd(
        path="/data/projects/dst123_metadata.yaml",
        nerd_dict={
            "name": "Mustermann, Max",
            "ldap_name": "mmuster",
            "department": "AG-mustermann",
            "email": "max.mustermann@mpi-bn.mpg.de",
        },
    )


Searching
----------

get_search_mask
^^^^^^^^^^^^^^^^

Return the search UI structure derived from the metadata schema.

.. code-block:: python

    from fred.src.wi_functions import get_search_mask

    mask = get_search_mask(pgm_object)

find_metadata
^^^^^^^^^^^^^^

Search for metadata files matching a search string. Returns a list of matching file records.

.. code-block:: python

    from fred.src.wi_functions import find_metadata

    results = find_metadata(
        config="/path/to/config.yaml",
        path="/data/projects",
        search_string='organism_name:"Homo_sapiens"',
    )

get_meta_info
^^^^^^^^^^^^^^

Return an HTML summary and the raw metadata for one or more project IDs.

.. code-block:: python

    from fred.src.wi_functions import get_meta_info

    html_str, metafile = get_meta_info(
        config="/path/to/config.yaml",
        path="/data/projects",
        project_ids=["dst123", "dst456"],
    )

get_meta_info_from_object
^^^^^^^^^^^^^^^^^^^^^^^^^^

Return an HTML metadata summary directly from an already-loaded metadata object.

.. code-block:: python

    from fred.src.wi_functions import get_meta_info_from_object

    html_str = get_meta_info_from_object(object)

parse_search_string_to_query
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Parse a FRED search string (same syntax as ``fred find -s``) into a query dictionary.

.. code-block:: python

    from fred.src.wi_functions import parse_search_string_to_query

    query = parse_search_string_to_query(
        search_string='organism_name:"Homo_sapiens" and tissue:"lung"',
        structure=pgm_object["structure"],
    )

get_text_keys
^^^^^^^^^^^^^^

Return all text-type keys from the metadata structure as dotted-path strings.

.. code-block:: python

    from fred.src.wi_functions import get_text_keys

    keys = get_text_keys(pgm_object["structure"])

get_all_query
^^^^^^^^^^^^^^

Build a list of regex query fragments for searching ``value`` across all given ``keys``.

.. code-block:: python

    from fred.src.wi_functions import get_all_query

    query_parts = get_all_query(keys, value)


Visualization
--------------

get_plot_from_object
^^^^^^^^^^^^^^^^^^^^^

Generate heatmap plots from an already-loaded metadata object. Returns a list of ``{"title": ..., "plot": <html>}`` dictionaries.

.. code-block:: python

    from fred.src.wi_functions import get_plot_from_object

    plots = get_plot_from_object(pgm_object, object)

get_plot
^^^^^^^^^

Generate heatmap plots for a project by searching for its metadata file first.

.. code-block:: python

    from fred.src.wi_functions import get_plot

    plots = get_plot(pgm_object, config, path, project_id)

download_plot
^^^^^^^^^^^^^^

Export heatmap plots as PNG files and return a list of saved filenames.

.. code-block:: python

    from fred.src.wi_functions import download_plot

    filenames = download_plot(pgm_object, finished_yaml, save_path)


Editing
--------

edit_wi_object
^^^^^^^^^^^^^^^

Start an interactive editing session for an existing metadata file and return the updated object.

.. code-block:: python

    from fred.src.wi_functions import edit_wi_object

    updated = edit_wi_object(path, pgm_object, read_in_whitelists)
