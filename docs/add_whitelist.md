## Whitelist storage

The whitelists for the project are located in the git repository inside the 'whitelists' folder. All newly created whitelist files must also be placed in this folder so that the metadata tool can read them.

The naming of the whitelists is identical to the key for which it is created. For example, the whitelist for the key 'organism' is also named 'organism'. 

## Whitelist types

In the Project there are three different ways to file whitelists. The default is 'plain text', where the whitelist elements are listed one below the other in lines.
Another option is 'group', where the whitelist items can be divided into subgroups to improve clarity.
Finally, whitelists can be made dependent on input for other keys using the whitelist type 'depend'. This is useful e.g. for genes, which can be made dependent on the examined organism.

### Type 1: plain text

This type of whitelist is the simplest, as it contains all values in plain text format. One line of the text document corresponds to one value in the whitelist.

#### Example

TBA

### Type 2: group

TBA

### Type 3: depend

This type of whitelist is used when the values depend on the input of another key in the metadata structure. 
The whitelist is organized here using a yaml file. Each whitelist of type 'depend' must contain the keys 'whitelist_type' and 'ident_key'.
The 'whitelist_type' is set with the value 'depend'. This identifies how the whitelist must be read within the metadata tool.
The key 'ident_key' names the key on whose input the whitelist should depend. For example, if you want to make the whitelist for genes dependent on the examined organism, you set the value for 'ident key' to 'organism'.

The possible elements of the 'ident_key' are then specified as further keys. For the 'ident_key' 'organism' possible keys would be 'human', 'mouse', 'zebrafish' etc. For each of these keys the whitelist can be entered as a list.
If the whitelists per key are very long, it makes sense to separate them into individual files. In this case the path to the whitelist within the folder 'whitelists' is specified as value instead of the whitelist itself. Since the path to the whitelist is specified explicitly, the naming of the whitelist can differ from the key and be chosen by the user. The whitelists can also be organized in subfolders.

If independent whitelist files already exist for the keys, those keys can be omitted and the metadata tool reads the existing files as whitelist. This is e.g. the case for the whitelist 'value'. The key 'value' in the metadata structure contains the examined values of the examined experimental factor. So the whitelist for 'value' depends on the whitelist 'factor'. Since each experimental factor has its own whitelist, the keys for the experimental factors in the whitelist for 'value' can be omitted. Thus, the existing files are read in as whitelist.


#### Example

TBA

# Adding values to a whitelist

The whitelists are located in the git repository in the folder whitelists. The whitelist file is named after the key in the metadata structure for which a whitelist should be available. 

To add a value to an existing whitelist, search the whitelist folder for the desired whitelist named after the key and open it.
If the opened whitelist is of type 1, add the new value in a new line.

# Adding a new whitelist
