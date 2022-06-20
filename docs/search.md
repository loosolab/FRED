# File Searching

## Programm Call

MetaTools includes a function to find metadata files using a search string over a specified path.

The find function of metaTools is called via
```bash
$ python metaTools.py find
```

with these arguments:

`-p, --path` the path over which to search

`-s, --search` the search string

To show the correct usage of the function, as well as all possible arguments in a help message, the function can also be called with the parameter:

`-h, --help` show help message

## Defining a search string

The search string must be enclosed in single quotes. It contains the values to be searched for. The values can be linked via 'and', 'or' and 'not'.
The link 'and' corresponds to a logical and, the link 'or' to a logical or. By placing a 'not' in front of the stated value, all values are searched for that do not correspond to the stated value.

__Examples:__

`-s 'human_9606'` search for files that contain human_9606 

`-s 'not human_9606'` search for files that do not contain human_9606 

`-s 'human_9606 and mouse_10090'` search for files that contain human_9606 and mouse_10090

`-s 'human_9606 or mouse_10090'` search for files that contain human_9606 or mouse_10090

### Increase accuracy

Specifying a simple value, such as 'human_9606' in the search string will cause all fields within the yaml file to be searched for the value.
If only a specific field should contain the searched value, a key can be specified to limit the search. The key is placed in front of the value and separated from the value with a colon. 

e.g.

`-s 'organism:human_9606'` searches for Files that contain humam_9606 as organism

Multiple keys can also be chained together with colons to narrow the search even further. However, it should be noted that the order of the keys must match the indentations within the underlying yaml structure.

__Example:__

The following yaml shows the structur of the keys for the project part.

```yaml
project:
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
```
`-s 'Jasmin Walter'` search for 'Jasmin Walter' in all fields

`-s 'name:Jasmin Walter'` search for 'Jasmin Walter' in all name fields

`-s 'owner:name:Jasmin Walter'` search for 'Jasmin Walter' in all name field of owner

`-s 'project:name:Jasmin Walter'` no functional search string, because the order of the keys within the underlying yaml structure is not met, functional alternatives are `-s 'project:owner:name:Jasmin Walter'` or `-s 'project:nerd:name:Jasmin Walter'`

### Using brackets

#### Round brackets

Round brackets in the search string are used to specify the order of evaluation.

If search strings are concatenated with 'and' and 'or', 'and' is normally evaluated first.

e.g. 

`gender:female or gender:male and organism:human_9606` 

is evaluated as 

`gender:female or (gender:male and organism_name:human)`

To explicitly specify the order in which the individual search terms are to be evaluated, round brackets can be integrated in the search string. The content within the round brackets is then evaluated first. Several round brackets can also be nested within each other.

