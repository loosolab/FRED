Add a new experimental factor
==============================

To add an experimental factor to the basic structure, five steps are necessary, which are explained below with an example.
In this example, we want to add a new experimental factor that can be used to specify injuries. We want to add two pieces of information for each injury: a status and an injury type.

Step 1: Add experimental factor to general structure
------------------------------------------------------

In the first step, the new experimental factor ``injury`` must be added to ``keys.yaml``. The key should serve as a heading for a new section containing the subordinate keys ``injury_status`` and ``injury_type``.
For the key ``injury`` the instructions from :ref:`section-a` in :doc:`add_keys` have to be followed. The position for experimental factors is fixed in ``keys.yaml``. They must be located within ``experimental_setting`` under ``conditions``, ``biological_replicates``, and there under ``samples`` in the key ``value``. Within the keys in ``value`` the new experimental factor should be placed below the mandatory fields ``sample_name``, ``pooled``, and ``number_of_measurements``, and above ``donor_count`` and ``technical_replicates`` to maintain clarity. After following the steps described in :ref:`section-a` in :doc:`add_keys`, the resulting structure in ``keys.yaml`` is shown below.

.. code-block:: yaml

    experimental_setting:
      ...
      value:
        ...
        conditions:
          ...
          value:
            ...
            biological_replicates:
              ...
              value:
                ...
                samples:
                  ...
                  value:
                    sample_name:
                      ...
                    pooled:
                      ...
                    number_of_measurements:
                      ...
                    injury:
                      mandatory: False
                      list: True
                      display_name: 'Injury'
                      desc: ''
                      value:

                    donor_count:
                      ...
                    technical_replicates:
                      ...

Now the keys ``injury_status`` and ``injury_type`` must be added under ``value`` in the key ``injury``. A user input is expected for these keys, so the instructions from :ref:`section-b` in :doc:`add_keys` must be followed for each key. The following snippet shows the resulting structure.

.. code-block:: yaml

    experimental_setting:
      ...
      value:
        ...
        conditions:
          ...
          value:
            ...
            biological_replicates:
              ...
              value:
                ...
                samples:
                  ...
                  value:
                    sample_name:
                      ...
                    pooled:
                      ...
                    number_of_measurements:
                      ...
                    injury:
                      mandatory: False
                      list: True
                      display_name: 'Injury'
                      desc: ''
                      value:
                        injury_status:
                          mandatory: True
                          list: False
                          display_name: 'Status'
                          desc: ''
                          value: null
                          whitelist: True
                          input_type: select
                        injury_type:
                          mandatory: False
                          list: False
                          display_name: 'Type'
                          desc: ''
                          value: null
                          whitelist: True
                          input_type: select
                    donor_count:
                      ...
                    technical_replicates:
                      ...

Step 2: Add experimental factor to the ``factor`` whitelist
------------------------------------------------------------

In the second step, the new experimental factor must be added to the whitelist ``factor``. The steps required for this are described in more detail under :doc:`add_whitelist_values`.
The new factor ``injury`` is added to the appropriate group in the whitelist for ``factor``. Since injuries are a type of treatment, it is added under ``treatments``:

.. code-block:: yaml

    whitelist_type: group
    whitelist:
        genetic:
        - genetic_background
        - gene_editing
        enrichments:
        - enrichment
        treatments:
        - medical_treatment
        - physical_treatment
        - temperature_treatment
        - injury
        biological factors:
        - tissue
        - cell_type
        - cell_line
        - strain
        - cellular_compartment
        - disease
        - gender
        - life_stage
        - age
        - ethnicity
        - body_type
        - body_mass_index
        other:
        - concentration
        - time_point
        - signal

Step 3: Add abbreviation of experimental factor
-------------------------------------------------

In the third step, an abbreviation must be added to the abbreviation whitelist of ``factor`` for the experimental factor added in the whitelist. The steps for this are also explained under :doc:`add_whitelist_values`. The abbreviated whitelist containing the added value is shown below:

.. code-block:: yaml

    whitelist_type: abbrev
    whitelist:
        genetic_background: gnb
        gene_editing: ge
        cell_line: cll
        tissue: tis
        cell_type: clt
        gender: gnd
        life_stage: lfs
        ethnicity: eth
        disease: dis
        medical_treatment: mtrt
        temperature_treatment: tempt
        time_point: tmp
        enrichment: enr
        body_mass_index: bmi
        body_type: bt
        injury: inj
        cellular_compartment: ccmp
        physical_treatment: ptrt
        strain: str
        signal: sgl
        concentration: conc

Since the experimental factor for injuries includes not only the key ``injury``, but also ``injury_status`` and ``injury_type`` underneath, these must also be abbreviated. The abbreviation of ``injury`` has already been done in the abbreviation whitelist for ``factor``. For the subordinate keys a new abbreviation whitelist must be created. This is named after the key under which the abbreviated keys are placed. In this example it is ``injury``. The creation of the whitelist is explained in more detail in :doc:`add_whitelist`. The resulting abbreviation whitelist ``injury`` looks like this:

.. code-block:: yaml

    whitelist_type: abbrev
    whitelist:
        injury_status: sts
        injury_type: tp

Step 4: Create new whitelists for values of experimental factor
----------------------------------------------------------------

In the fourth step, new whitelists are now created for the values of the experimental factor. It is recommended to create whitelists for the values of all experimental factors if they expect a string input.
Since the factor ``injury`` is split into ``injury_status`` and ``injury_type``, a whitelist is created for the values of these two keys. Instructions on how to do this can be found under :doc:`add_whitelist`. The following table shows the newly created whitelists:

**injury_status:**

.. code-block:: yaml

    whitelist_type: plain
    whitelist:
        - non-injured
        - injured

**injury_type:**

.. code-block:: yaml

    whitelist_type: plain
    whitelist:
        - cryoinjury
        - tac
        - cardiotoxin injection
        - sham
        - amputation

Step 5: Create abbreviations for the new whitelist values
----------------------------------------------------------

In the last step, abbreviation whitelists are created for the newly defined possible values in the whitelist of the experimental factor. The procedure for this is described under :doc:`add_whitelist`. The following table shows the abbreviation whitelists for ``injury_status`` and ``injury_type``:

**whitelists/abbrev/injury_status:**

.. code-block:: yaml

    whitelist_type: abbrev
    whitelist:
        non-injured: ninj
        injured: inj

**whitelists/abbrev/injury_type:**

.. code-block:: yaml

    whitelist_type: abbrev
    whitelist:
        cryoinjury: cryo
        cardiotoxin injection: ctx
        amputation: amp
