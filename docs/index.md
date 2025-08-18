# How to install

### Requirements

The requirements can be installed directly via pip or within a conda environment.

Python>=3.6

__Python Packages:__

- PyYAML>=5.1
- tabulate>=0.8.10

### Setting up a conda environment

The following steps show how to set up a conda environment:

1\. Create a conda environment with the name 'metadata'. Type 'y' when conda asks you to proceed.

```bash
conda create -n metadata
```

2\. Install the requirements into the 'metadata' environment. Type 'y' when conda asks you to proceed.

```bash
conda install -n metadata "pyyaml>=5.1" "tabulate>=0.9.0" "GitPython>=3.1.18" "pytz>=2022.2.1" "python-dateutil>=2.8.2"
```

3\. Activate the 'metadata' environment to use the metadata tool.

```bash
conda activate metadata
```

When you are done using the metadata tool, you can disable the environment via:

```bash
conda deactivate
```


### Clone the repository

To use the tool, the repository must first be cloned from git 

via HTTPS:
```bash
git clone https://github.com/loosolab/FRED.git
```

or via SSH:
```bash
git clone git@github.com:loosolab/FRED.git
```

Then navigate to the metadata-organizer folder where the executable python file metaTools.py is located via:

```bash
cd metadata-organizer
```

MetaTools has two basic functions.

Firstly, it has a function to generate metadata. More information about the usage of this function can be found under [File Generation](generate.md).

Secondly, there is a function to search within a given path for all metafiles that contain a specified search string. Information about the call, parameters and the creation of a search string can be found under [File Searching](search.md).
