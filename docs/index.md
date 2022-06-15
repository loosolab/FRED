# How to install

### Requirements

The requirements can be installed directly or within a conda environment.

Python>=3.6

__Python Packages:__

- PyYAML~=3.12
- Columnar~=1.4.1

### Clone the repository

To use the tool, the repository must first be cloned from git via:

```bash
git clone https://gitlab.gwdg.de/loosolab/software/metadata-organizer.git
```

Then navigate to the metadata-organizer folder where the executable python file metaTools.py is located via:

```bash
cd metadata-organizer
```

MetaTools has two basic functions.

Firstly, it has a function to generate metadata. More information about the usage of this function can be found under [File Generation](generate.md).

Secondly, there is a function to search within a given path for all metafiles that contain a specified search string. Information about the call, parameters and the creation of a search string can be found under [File Searching](search.md).
