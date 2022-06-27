# General structure

The data structure used for the metadata is stored in the repository as the template keys.yaml. It contains all valid keys within the data structure. 

For each key, its properties are stored within a list. The keys are distinguished between inner nodes and leaf nodes. Leaf nodes have the same properties as inner nodes, but in addition whitelist, input type and data type are defined for them.

The following properties are defined for each key in the specified order:

Position | Description | Value
-------- | -------- | --------
1   | A boolean value indicating weather the key is mandatory   | True/False
2   | A boolean value indicating weather the key is a list   | True/False
3   | A name to describe the key    |  '[name]' or '' if there is no name
4   | A text to descripe the key    |  '[description]' or '' if there is no description
5   | A default value to the key    |  '[value]' or None or [key]:[properties] if the value is a dictionary
6   | A boolean value indicating whether there is a whitelist of allowed values for the value of the key | True/False
7   | The HTML input type for the key value | input type
8   | The HTML data type for the key value | data type

The properties 6-8 are only be specified for leaf nodes.

# Included keys

```yaml
project:
    id:
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

experimental_setting:
    organism:
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
                genotype:
                gender:
                life_stage:
                age:
                    value:
                    unit:
                ethnicity:
                tissue:
                cell_type:
                gene:
                disease_information:
                    healthy:
                    disease:
                        disease_status:
                        disease_type:
                        disease_stage:
                treatment_information:
                    treated:
                    treatment:
                        treatment_status:
                        treatment_type:
                        treatment_duration:
                            value:
                            unit:
                time_point:
                    value:
                    unit:
                flow:
                knockdown:
                donor_count:
                technical_replicates:
                    count:
                    sample_name:
                        
technical_details:
    technique:
    analysis:
        sample_preparation:
        further_description:
        runs:
            date:
            reference_genome:
            parameters:
            output:
```
