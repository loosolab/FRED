# Adding a new whitelist

To add a new whitelist, you must first specify its type. Basically, every whitelist can be represented in type 'plain'. So if you are not sure which type fits to the whitelist values, you can always resort to this type.
If a whitelist contains many values, which can be divided thematically into subgroups, then it serves the overview, if you create a whitelist of the type 'group' and assign the whitelist values to the appropriate topics.
If a whitelist depends on the input of another key, the type 'depend' must be used to represent this dependency. 
A detailed explanation of the individual whitelist types can be found in section [Whitelists](whitelists.md). In the following, the creation of a whitelist for the individual types is described.

#### plain

A whitelist of type 'plain' contains two keys that must be specified. The first key is the 'whitelist_type' and is set with the type 'plain'. The second key 'whitelist' contains the possible values that the key for which the whitelist is created can take. The adding of the values works in the same way as it is already explained under '[Add values to whitelist](add_whitelist_values.md)'.

```yaml
whitelist_type: 'plain'
whitelist:

```

#### group

A grouped whitelist also contains the key 'whitelist_type', which is set to 'group'. Under the key 'whitelist', the possible values are then specified as a dictionary, where the keys are synonymous with the thematic subdivisions. An instruction for adding the values in a grouped whitelist is already described under '[Add values to whitelist](add_whitelist_values.md)'.

```yaml
whitelist_type: 'group'
whitelist:

```

#### depend

A dependent whitelist is needed when the possible values depend on the input value of another key. Again the 'whitelist_type' is defined, in this case with 'depend'. A key that has to be defined additionally in this kind of whitelists is an 'ident_key'. This contains the name of the key on whose input value the whitelist depends, in the same syntax as it was specified in the 'keys.yaml'. For example, if the whitelist values depend on the organism name, the value 'organism_name' is entered here. It is important to note that the key on which the whitelist values are dependent must appear before the key for which the whitelist is defined in the 'keys.yaml'. Since the metadata is entered in the same order as it is specified in the basic structure, it can otherwise happen that the value on which the whitelist depends has not yet been entered.
Under the key 'whitelist' the whitelist values are stored just like with the other types. In dependent whitelists these are stored as a dictionary, where the keys correspond to the possible values of the 'ident_key'. Instructions for adding values to such a whitelist can also be found under '[Add values to whitelist](add_whitelist_values.md)'.

```yaml
whitelist_type: 'depend'
ident_key: 'organism_name'
whitelist:

```

#### abbrev

An abbreviation whitelist is located inside the 'whitelists' folder in the subfolder 'abbrev' and is named after the key for whose values it contains a whitelist. Per whitelist the 'whitelist_type' is defined again, in this case with 'abbrev'. Under the key 'whitelist' all values are specified as key, which should be abbreviated, as well as their abbreviations. Detailed instructions for adding values are described under '[Add values to whitelist](add_whitelist_values.md)'.

```yaml
whitelist_type: 'abbrev'
whitelist:

```

