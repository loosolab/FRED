General structure
===================

The data structure used for the metadata is stored in the repository as the template keys.yaml. It contains all valid keys within the data structure. 

For each key, its properties are stored within a list. The keys are distinguished between inner nodes and leaf nodes. Leaf nodes have the same properties as inner nodes, but in addition whitelist, input type and data type are defined for them.

The following properties are defined for each key in the specified order:

.. list-table::
   :width: 100%
   :widths: 20 30 30
   :header-rows: 1

   * - Property
     - Description
     - Value
   * - mandatory
     - True/False
     - A boolean value indicating weather the key is mandatory 
   * - list
     - True/False
     - A boolean value indicating weather the key is a list
   * - display_name
     - '[name]' or '' if there is no name
     - A name to describe the key
   * - desc
     - '[description]' or '' if there is no description
     - A text to descripe the key
   * - value
     - '[value]' or None or [key]:[properties] if the value is a dictionary
     - A default value to the key
   * - whitelist
     - True/False
     - A boolean value indicating whether there is a whitelist of allowed values for the value of the key
   * - input_type
     - input type
     - The input type for the key value

The properties 'whitelist' and 'input_type' are specified only for keys that expect direct user input.
Detailed instructions on how to add the properties for new keys can be found under :doc:`add_keys`.

Included keys
--------------

The following extract shows all keys that have already been created in the metadata structure under 'keys.yaml'.


.. code-block:: yaml

    project:
        id:
        project_name:
        date:
        description:
        further_description:
        graphical_abstract:
        publication:
            pubmed_id:
            title:
            year:
            author:
            journal:
            volume:
            issue:
            pages:
            doi:
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

    experimental_setting:
        setting_id:
        organism:
            organism_name:
            taxonomy_id:
        experimental_factors:
            factor:
            values:
        conditions:
            condition_name:
            biological_replicates:
                count:
                samples:
                    sample_name:
                    pooled:
                    donor_count:
                    number_of_measurements:
                    gene_editing:
                        editing_type:
                        editing_method:
                        gene:
                            gene_name:
                            ensembl_id:
                        modification:
                    genetic_background:
                    enrichment:
                        enrichment_type:
                        modification:
                    injury:
                        injury_status:
                        injury_type:
                    medical_treatment:
                        treatment_type:
                        treatment_status:
                        treatment_duration:
                            value:
                            unit:
                        treatment_amount:
                            value:
                            unit:
                    physical_treatment:
                    temperature_treatment:
                        treatment_status:
                        temperature:
                            value:
                            unit:
                        treatment_duration:
                            value:
                            unit:
                    age:
                        value:
                        unit:
                    body_type:
                    body_mass_index:
                        value:
                        unit:
                    cell_line:
                    cell_type:
                    cellular_compartment:
                    disease:
                        disease_type:
                        disease_status:
                        disease_stage:
                        disease_risk:
                    ethnicity:
                    gender:
                    life_stage:
                    strain:
                    tissue:
                    concentration:
                        value:
                        unit:
                    signal:
                    time_point:
                        value:
                        unit:
                    technical_replicates:
                        count:
                        sample_name:
                        filenames:

    technical_details:
        techniques:
            setting:
            technique:
        analysis_runs:
            date:
            reference_genome:
            parameters:
            output:
        sample_preparation:
        further_description:

