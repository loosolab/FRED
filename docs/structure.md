# General structure

The data structure used for the metadata is stored in the repository as the template keys.yaml. It contains all valid keys within the data structure. 

For each key, its properties are stored within a list. The keys are distinguished between inner nodes and leaf nodes. Leaf nodes have the same properties as inner nodes, but in addition whitelist, input type and data type are defined for them.

The following properties are defined for each key in the specified order:

Property | Description | Value
-------- | -------- | --------
mandatory | True/False  | A boolean value indicating weather<br>the key is mandatory   
list  | True/False |      A boolean value indicating weather<br>the key is a list   
display_name   |          '[name]' or '' if there <br>is no name | A name to describe the key   
desc  |  '[description]' or '' if <br>there is no description | A text to descripe the key    
value |  '[value]' or None or <br>[key]:[properties] if the<br>value is a dictionary  | A default value to the key    
whitelist  | True/False | A boolean value indicating whether<br>there is a whitelist of allowed <br>values for the value of the key 
input_type  | input type | The input type for the key value 

The properties 'whitelist' and 'input_type' are specified only for keys that expect direct user input.
Detailed instructions on how to add the properties for new keys can be found under [Add keys](add_keys.md).

# Included keys

The following extract shows all keys that have already been created in the metadata structure under 'keys.yaml'.

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
                injury:
                    injury_status:
                    injury_type:
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
                body_mass_index:
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
