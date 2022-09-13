# Adding a key to the structure

To add a key to the data structure the file keys.yaml must be edited. The key must then be added at the appropriate position with the appropriate indentation. The properties of the new key must be specified. For this purpose, the structure described in [General structure](structure.md) must be adopted. It is important to note that all 8 properties should only be specified for leaf nodes. If the new key is an inner node, i.e. it contains further keys as value, then only property 1-5 are specified, whereby property 5 (default value) is given the further keys as value.

### Example

The following code fragment shows a section of the 'keys.yaml'. You can see the 'project' part, which contains an 'id'. 
In this example, a key 'owner' is first added to the 'project' part. Afterwards a key 'name' is added to the key 'owner'.

```yaml
project:
  - 'mandatory'
  - False
  - 'Project'
  - 'This part contains general information about the project.'
  - id:
      - 'mandatory'
      - False
      - 'ID'
      - ''
      - null
      - False
      - short_text
      - str
```

To add the key 'owner' to keys.yaml, you first have to find the place where you want to add it. In this example the 'owner' key should be on the same level as 'id' and is therefore added in the same list element as 'id' and with the same indentation.

```yaml
project:
  - 'mandatory'
  - False
  - 'Project'
  - 'This part contains general information about the project.'
  - id:
      - 'mandatory'
      - False
      - 'ID'
      - ''
      - null
      - False
      - short_text
      - str
    owner:
```

After that the properties of the key 'owner' have to be added one after the other in a list:

__1. Is the key mandatory or optional?__

Der key 'owner' ist in diesem Beispiel mandatory. Aus diesem Grund adden wir als erstes Listenelement den String 'mandatory'.

```yaml
    owner:
      - 'mandatory'
```

__2. Is it a list?__

This item tells whether the key should be treated as a list when filling in the structure. Since there is only one owner for a project, we add False to the properties.

```yaml
    owner:
      - 'mandatory'
      - False
```

__3. Display name__

This property specifies as a string how the key should be displayed later in the command line or web interface. In this example, we set the owner with a capital first letter to beautify the display.

```yaml
    owner:
      - 'mandatory'
      - False
      - 'Owner'
```

__4. Description__

This element of the property list specifies a description of the key as it should be displayed in the comman line or web interface. If the key is self-explanatory and does not require a description, an empty string '' can be specified here. In the example we give the following description for the owner: 'The owner manages the project and acts as the first point of contact for questions'.
 
```yaml
    owner:
      - 'mandatory'
      - False
      - 'Owner'
      - 'The owner manages the project and acts as the first point of contact for questions'
```

__ 5. Value__

TBA
