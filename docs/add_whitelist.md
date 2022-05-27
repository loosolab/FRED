# Whitelist types

Two types of whitelists are used in this project. 

### Type 1: plain text

This type of whitelist is the simplest, as it contains all values in plain text format. One line of the text document corresponds to one value in the whitelist.

#### Example

TBA

### Type 2: yaml file

This type of whitelist is used when the values depend on another key in the metadata structure. The information on which key the whitelist depends is specified in the 'ident_key' inside the whitelist.
An example of a dependent whitelist is the whitelist for genes. Genes are different per organism, which is why the gene whitelist is subdivided by organism. The organisms are represented as keys within the whitelist. For each organism key there is a list with the corresponding genes as value.


#### Example

TBA

# Adding values to a whitelist

The whitelists are located in the git repository in the folder whitelists. The whitelist file is named after the key in the metadata structure for which a whitelist should be available. 

To add a value to an existing whitelist, search the whitelist folder for the desired whitelist named after the key and open it.
If the opened whitelist is of type 1, add the new value in a new line.

# Adding a new whitelist
