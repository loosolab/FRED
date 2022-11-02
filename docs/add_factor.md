# Add a new experimental factor

To add an experimental factor to the basic structure, the five steps are necessary, which are explained below with an example. 
In this example, we want to add a new experimental factor that can be used to specify injuries. We want to add two pieces of information for each injury, one is a status and the other is an injury type.

### Step 1: Add experimental factor to general structure

In the first step, the new experimental factor 'injury' must be added to 'keys.yaml'. The key should serve as a heading for a new section containing the subordinate keys 'injury_status' and 'injury_type'.
For the key 'injury' the instructions from section A on adding keys have to be followed. The position for experimental factors is fixed in the 'keys.yaml'. They must be located within the 'experimental_setting' under 'conditions',  'biological_replicates' and there under 'samples' in the key 'value'. Within the keys in 'value' the new experimental factor should be below the mandatory fields 'sample_name'. 'pooled' and 'number_of_measurements' and above 'donor_count' and 'technical_replicates' to maintain clarity. After following the steps described in section A, the resulting structure in 'keys.yaml' is shown below. 

```yaml
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
```

Now the keys 'injury_status' and 'injury_type' must be added under 'value' in the key 'injury'. A user input is expected for these keys, so the instructions from section B for adding keys must be followed for each key. The following snippet shows the resulting structure.

```yaml
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
```

TODO: special case group

### Step 2: Add experimental factor to 'factor' whitelist

### Step 3: Add abbreviation of experimental factor

### Step 4: Create new whitelist for values of experimental factor

### Step 5 Create abbreviations for the new whitelist values
