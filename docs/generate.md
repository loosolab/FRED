# File Generation

MetaTools has a function to generate a metadata file. Information is requested from the user in a dialog and entered into a yaml structure.

The generate function of metaTools is called via
```bash
$ python metaTools.py generate
```

with these arguments:

`-p, --path` the path where the files of the experiment are located and to which the yaml file should be saved

`-id, --id` the ID of the experiment

`-n, --name` the name of the experiment

The Generate function also has a mode in which only mandatory keys are requested. In this mode the metadata input will be accelerated. The mode can be initiated by the following argument:

`-mo, --mandatory_only` mandatory only mode

To show the correct usage of the function, as well as all possible arguments in a help message, the function can also be called with the parameter:

`-h, --help` show help message
