# FRED

<img align="right" width=250 src="docs/images/fred_logo.png">

Introduction 
------------

Scientific research relies on transparent dissemination of data and its associated interpretations. This task encompasses accessibility of raw data, its metadata, details concerning experimental design, along with parameters and tools employed for data interpretation. Production and handling of these data represents an ongoing challenge, extending beyond publication into individual facilities, institutes and research groups, often termed Research Data Management (RDM). It is foundational to scientific discovery and innovation, and can be paraphrased as Findability, Accessibility, Interoperability and Reusability (FAIR). Although the majority of peer-reviewed journals require the deposition of raw data in public repositories in alignment with FAIR principles, metadata frequently lacks full standardization. This critical gap in data management practices hinders effective utilization of research findings and complicates sharing of scientific knowledge. Here we present a flexible design of a machine-readable metadata format to store experimental metadata, along with an implementation of a generalized tool named **FRED** (**F**ai**R** **E**xperimental **D**esigns). It enables i) dialog based creation of metadata files, ii) structured semantic validation, iii) logical search, iv) an external programming interface (API), and v) a standalone web-front end. The tool is intended to be used by non-computational scientists as well as specialized facilities, and can be seamlessly integrated in existing RDM infrastructure.


For more information about FRED, please see the [documentation](https://loosolab.pages.gwdg.de/software/metadata-organizer/).


# How to install


## Via Python package
--------------------

FRED is published in the Python Package Index (PyPI) under the name [fred-metadata](https://pypi.org/project/fred-metadata/). It can be installed with the following command:

```
pip install fred-metadata
```


## Via Repository

You can install FRED directly from the repository with the following commands:

1. Clone the repository 

```
git clone https://github.com/loosolab/FRED.git
```

2. Move to the new repository directory

```
cd FRED
```

3. (Optional) Create and activate a pip environment

```
python3 -m venv .venv
source .venv/bin/activate
```

4. Install the package

```
pip install .
```

# Standalone Version

The standalone web-frontend is provided in a separate Repository. You can find it here:

https://github.com/loosolab/FRED_standalone
