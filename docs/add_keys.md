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

# Adding a key to the structure

To add a key to the data structure the file keys.yaml must be edited. The key must then be added at the appropriate position with the appropriate indentation. The properties of the new key must be specified. For this purpose, the structure described in General structure must be adopted. It is important to note that all 8 properties should only be specified for leaf nodes. If the new key is an inner node, i.e. it contains further keys as value, then only property 1-5 are specified, whereby property 5 (default value) is given the further keys as value.

### Example

TBA
