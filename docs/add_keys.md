# Adding a key to the structure

To add a key to the data structure the file [keys.yaml](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/blob/main/keys.yaml) must be edited. The key must then be added at the appropriate position with the appropriate indentation. The properties of the new key must be specified. For this purpose, the structure described in [General structure](structure.md) must be adopted. It is important to note that all seven properties should only be specified for keys that actually expect an input as a value. If the new key is only used to separate a section, i.e. it contains other keys as value, then only the first five properties are specified.

### Example

The following code fragment shows a section of the '[keys.yaml](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/blob/main/keys.yaml)'. You can see the 'project' part, which contains an 'id'. 
In this example, first a key "owner" is added to the 'project' part to create a new subsection. Step-by-step instructions are given in section [A](#a:-adding-a-key-as-section). Then, a key 'name' is added to the 'owner' section, which expects input from the user. The instructions for adding this key are described in section [B](#b:-adding-a-key-with-value).

```yaml
project:
  mandatory: True
  list:  False
  display_name: 'Project'
  desc: 'This part contains general information about the project.'
  value:
    id:
      mandatory: True
      list: False
      display_name: 'ID'
      desc: ''
      value: null
      whitelist: False
      input_type: 'short_text'
```

#### A: Adding a key as section

To add the key 'owner' to [keys.yaml](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/blob/main/keys.yaml), you first have to find the place where you want to add it. In this example the 'owner' key should be on the same level as 'id' and is therefore added in the same list element as 'id' and with the same indentation.

```yaml
project:
  mandatory: True
  list:  False
  display_name: 'Project'
  desc: 'This part contains general information about the project.'
  value:
    id:
      mandatory: True
      list: False
      display_name: 'ID'
      desc: ''
      value: null
      whitelist: False
      input_type: 'short_text'
    owner:
```

After that the properties of the key 'owner' have to be added one after the other as a dictionary:

##### 1. Mandatory

The key 'owner' is mandatory in this example. For this reason we set the property 'mandatory' to True.

```yaml
    owner:
      mandatory: True
```

##### 2. List

This item tells whether the key should be treated as a list when filling in the structure. Since there is only one owner for a project, we set this property to False.

```yaml
    owner:
      mandatory: True
      list: False
```

##### 3. Display name

This property specifies as a string how the key should be displayed later in the command line or web interface. In this example, we set the 'display_name' to 'Owner' with a capital first letter to beautify the display.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
```

##### 4. Description

The element 'desc' of the property list specifies a description of the key as it should be displayed in the command line or web interface. If the key is self-explanatory and does not require a description, an empty string '' can be specified here. In the example we give the following description for the owner: 'The owner manages the project and acts as the first point of contact for questions'.
 
```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
```

##### 5. Value

The last property to be specified is 'value'. For keys that act as section headers, the subordinate keys are specified here. If the subordinate key is to contain further keys, the steps from section [A](#a:-adding-a-key-as-section) must be repeated in order to add it. If the user is expected to enter a value for the subordinate key, the steps from section [B](#b:-adding-a-key-with-value) must be followed to include it. In this example, a name is to be defined for the 'owner'. For the name a direct user input is required. Therefore, the steps in section [B](#b:-adding-a-key-with-value) must be followed to add the key 'name'.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
```

#### B: Adding a Key with value

To add a key, you must first find the appropriate position and indentation for it in the [keys.yaml](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/blob/main/keys.yaml). In this example we add a key 'name' to the 'owner' added in section A. It is placed inside the 'owner' under 'value'. 

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
```

After that the properties of the key 'name' have to be added one after the other as a dictionary:

##### 1. Mandatory

The name shall be specified for each owner for unique identification. For this reason the property 'mandatory' is set to True.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
```

##### 2. List

Each owner can only have one name. The property 'list' is therefore set to False.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
```

##### 3. Display name

For the property 'display_name' the name of the key is specified, as it should be displayed in the command line and in the web interface. For this example we enter 'Name' with an uppercase first letter.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
          display_name: 'Name'

```
##### 4. Description

The 'desc' property should contain a short explanation about the key and/or expected input values. If the input is self-explanatory, an empty string can be specified here. For this example, an explanation of the expected format for the name has been provided.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
          display_name: 'Name'
          desc: "The name should be entered in the format 'Last name, First name'. For public projects enter 'public'."
```

##### 5. Value

For the property 'value' a default value can be set at this point, which will then be entered in all metadata files, unless the user explicitly changes it. For the name of the owner a default value makes no sense, because every project has a different owner. For this reason 'value' is set to null.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
          display_name: 'Name'
          desc: "The name should be entered in the format 'Last name, First name'. For public projects enter 'public'."
          value: null
```

##### 6. Whitelist

The 'whitelist' property indicates whether a whitelist has been created for the key. If an input of type string is expected for the key, it may be useful to create a whitelist for its possible values at this point in order to standardize their syntax. An explanation of the purpose of whitelists can be found under '[Whitelists](whitelists.md)'. To add to that, '[Add new whitelist](add_whitelist.md)' contains instructions for creating new whitelists. 
For our example key 'name' a string input is expected, but it makes no sense to create a whitelist at this point, because a list with the names of possible owners would be difficult to keep up to date. For this reason, we specify False for the property 'whitelist' at this point.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
          display_name: 'Name'
          desc: "The name should be entered in the format 'Last name, First name'. For public projects enter 'public'."
          value: null
          whitelist: False
```

##### 7. Input_type


The 'input_type' property is used to specify the type of the value to be entered and how the input field should be displayed in the web interface. The following table summarizes all possible input types:

| input_type | value type | description |
| ----------- | ----------- | ----------- |
| select | String | The input type 'select' is selected if the input has a whitelist. In this case a drop-down menu is displayed in the web interface.  |
| short_text | String | The input type 'short_text' is used for string input without whitelist if it is not longer than one line. In the web interface an input field is displayed that contains one line. |
| long_text | String | The input type 'long_text' is used when a longer string input must be entered. It creates an input box in the web interface that can be adjusted in its size. |
| bool | Boolean | The input type 'bool' is used when a value of type Boolean is expected. The query of the values is controlled by a drop-down menu in the web interface. |
| number | Integer | The input type 'number' is used for values of type integer. In the web interface, an input field similar to 'short_text' is displayed, which only allows the input of numbers and contains two arrows that can be used to increase or decrease the entered value. |
| date | Date | The input type 'date' is used for dates. For this type, a calendar is displayed in the web interface, which can be used to select the corresponding date. |

For the name of the owner a string input is expected. Since the name has no whitelist and is presumably not longer than one line, the type 'short_text' is specified here.

```yaml
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
          display_name: 'Name'
          desc: "The name should be entered in the format 'Last name, First name'. For public projects enter 'public'."
          value: null
          whitelist: False
          input_type: 'short_text'
```

<hr>

The following snippet shows the general structure, which contains the new keys 'owner' and 'name' now that all entries have been made.

```yaml
project:
  mandatory: True
  list:  False
  display_name: 'Project'
  desc: 'This part contains general information about the project.'
  value:
    id:
      mandatory: True
      list: False
      display_name: 'ID'
      desc: ''
      value: null
      whitelist: False
      input_type: 'short_text'
    owner:
      mandatory: True
      list: False
      display_name: 'Owner'
      desc: 'The owner manages the project and acts as the first point of contact for questions'
      value:
        name:
          mandatory: True
          list: False
          display_name: 'Name'
          desc: "The name should be entered in the format 'Last name, First name'. For public projects enter 'public'."
          whitelist: False
          input_type: 'short_text'
```

