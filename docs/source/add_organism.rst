Add a new organism
===================

To add support for a new organism in FRED, four files in the `whitelist repository <https://github.com/loosolab/FRED_whitelists>`_ need to be updated. This guide walks through each step using the example of adding *Bos taurus* (cattle, taxonomy ID 9913).

Step 1: Add organism to the ``organism`` whitelist
----------------------------------------------------

Open the file ``whitelists/organism`` in the whitelist repository and add a new entry. The format is::

    Genus_species taxonomy_id

where ``Genus_species`` is the NCBI taxonomy name and ``taxonomy_id`` is the numeric NCBI taxonomy identifier. The ``organism_name`` used in all dependent whitelists is the part before the space (i.e. ``Genus_species``).

.. code-block:: yaml

    whitelist_type: plain
    headers: organism_name taxonomy_id
    whitelist:
        - Homo_sapiens 9606
        - Mus_musculus 10090
        - Danio_rerio 7955
        ...
        - Bos_taurus 9913    # newly added

Step 2: Add reference genomes to the ``reference_genome`` whitelist
--------------------------------------------------------------------

Open the file ``whitelists/reference_genome`` and add a new section for the organism. Since this whitelist is of type ``group``, add a new key with the organism's common name (matching the existing convention in that file) and list the available reference genome assemblies as values.

.. code-block:: yaml

    whitelist_type: group
    whitelist:
        human:
          - hg38
          - hg19
        mouse:
          - mm10
          - mm9
          - mm38
        ...
        cattle:
          - bosTau9
          - bosTau8

Step 3: Create a gene whitelist and register it in the ``gene`` whitelist
--------------------------------------------------------------------------

**3a.** Create a new file ``whitelists/genes/cattle`` containing one gene per line in the format ``SYMBOL_ENSEMBLID``:

.. code-block:: yaml

    whitelist_type: plain
    headers: gene_name ensembl_id
    whitelist:
        - A1CF_ENSBTAG00000000139
        - A2M_ENSBTAG00000001170
        ...

**3b.** Open ``whitelists/gene`` and add the new organism. The key must exactly match the ``organism_name`` from the ``organism`` whitelist (i.e. ``Bos_taurus``):

.. code-block:: yaml

    whitelist_type: depend
    ident_key: organism_name
    whitelist:
        Homo_sapiens: genes/human
        Mus_musculus: genes/mouse
        Danio_rerio: genes/zebrafish
        ...
        Bos_taurus: genes/cattle    # newly added

.. important::

    The key in the ``gene`` whitelist must be the exact NCBI taxonomy name (``Bos_taurus``), not a common name. This ensures it matches the ``organism_name`` field entered during metadata generation.

Step 4: Add abbreviation for the organism name
-----------------------------------------------

Open the file ``whitelists/abbrev/organism_name`` and add an abbreviation for the new organism. The abbreviation is used in auto-generated sample file names and may only contain letters and numbers.

.. code-block:: yaml

    whitelist_type: abbrev
    whitelist:
        Homo_sapiens: hsa
        Mus_musculus: mmu
        Danio_rerio: dre
        ...
        Bos_taurus: bta    # newly added

.. note::

    Make sure the abbreviation is unique across the entire whitelist and does not already appear for another organism.
