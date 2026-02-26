Whitelist storage
====================

The whitelists for the project are located in the Git repository `metadata_whitelists <https://github.com/loosolab/FRED_whitelists>`_ inside the 'whitelists' folder. All newly created whitelist files must also be placed in this folder so that FRED can read them.

The naming of the whitelists is identical to the key for which it is created. For example, the whitelist for the key 'organism' is also named 'organism'. 

The whitelist files have the format yaml. For each whitelist two mandatory keys must be specified. The first one is 'whitelist_type' and describes the nature of the whitelist and how it must be processed in the program. There are four different whitelist types, which are described in more detail in the sections below.
The second mandatory key is called 'whitelist' and contains the values that can be accepted by the metadata field for which the whitelist was created.

Whitelist types
=====================

Type 1: plain
-------------------

Whitelists of type plain are the simplest way to set values for a metadata field. A simple list of potential values is specified for the key whitelist. 

**Example:**

.. list-table::
   :width: 100%
   :widths: 50 

   * - whitelists/gender
   * - 
       .. code-block:: yaml
          
          whitelist_type: plain
          whitelist:
          - male
          - female
          - mixed


Type 2: group
-----------------

This whitelist type is used to group the values within the whitelist for better organization. Here, the key whitelist receives a dictionary as value, whose keys represent subheadings. For these keys, thematically matching values are then stored in a list. When generating the metadata, the whitelist values are output in the same grouping as defined in the whitelist file. The aim of this whitelist type is to improve the clarity when creating and extending the whitelists as well as when generating the metadata file.

**Example:**

.. list-table::
   :width: 100%
   :widths: 50 

   * - whitelists/disease_type
   * - The whitelist values for 'disease_type' were grouped based on the organs affected by the disease. 
       This allows faster finding of diseases in the list, as well as a better overview.
   * - 
       .. code-block:: yaml
          
          whitelist_type: group
          whitelist:
            lung:
            - lung cancer
            - COPD
            - PH
            ...
            heart:
            - Coronary heart disease CHD
            - Angina
            - Blood pressure
            ...
            other:
            - breast cancer
            - prostate cancer


Type 3: depend
-------------------

This type of whitelist is used when the values depend on the input of another key in the metadata structure. Each whitelist file of type depend contains beside 'whitelist_type' and 'whitelist' the further mandatory key 'ident_key'. This identifies the key in the metadata structure on whose input the whitelist should depend. For example, if you want to make the whitelist for genes dependent on the organism under investigation, set the value for 'ident_key' to 'organism_name'.
The key 'whitelist' receives a dictionary whose keys represent the possible values of the metadata field specified in 'ident_key'. These keys are then assigned the values in a list, which an input can accept depending on this key.


**Example:**

.. list-table::
   :width: 100%
   :widths: 50 50

   * - whitelists/reference_genome
     - whitelists/organism
   * - In this example, the whitelist for the reference genome is represented as depending on the organism.For this reason, the 'ident_key' is assigned 'organism_name'. 
       The possible organisms form the keys specified under 'whitelist'. Their values are those reference genomes that can be set for the respective organism.
       This allows faster finding of diseases in the list, as well as a better overview.
     - The whitelist for 'organism_name' contains all allowed organisms as values. These form the keys in the dependent whitelist 'reference_genome'.
   * - 
       .. code-block:: yaml
          
          whitelist_type: depend
          ident_key: organism_name
          whitelist:
            human_9606:
            - hg38
            - hg19
            mouse_10090:
            - mm10
            - mm9
            - mm38
            zebrafish_7955:
            - danrer11
            - danrer10
            ...
     
     
     -  
        .. code-block:: yaml
          
          whitelist_type: plain
          whitelist:
          - human_9606
          - mouse_10090
          - zebrafish_7955
          ...



Type 4: abbrev
--------------------

This type of whitelist must be provided for all experimental factors, their values, and for the organisms. The fields mentioned are those from which file names for samples are generated during metadata creation. Since file names are limited in length, the values must be shortened using the abbrev whitelist. In this process, all special characters are also removed from the values.
Whitelists of type abbrev are located inside the 'whitelists' folder in the 'abbrev' folder. They are named after the key for whose values they contain the abbreviations.  
Here a dictionary is passed to the key 'whitelist'. The keys of this dictionary correspond to the values of the non-abbreviated whitelist. Each key receives its abbreviated version. If an non-abbreviated value has only a short length and does not contain any special characters, it does not have to be specified in the abbrev whitelist. In such a case it will be included unchanged in the filename.

**Example:**

.. list-table::
   :width: 100%
   :widths: 50 

   * - whitelists/abbrev/gender
   * - In this example, the abbrev whitelist was created for the experimental factor gender.
   * - 
       .. code-block:: yaml
          
          whitelist_type: abbrev
          whitelist:
            male: m
            female: f
            mixed: x

  
.. list-table::
   :width: 100%
   :widths: 50 

   * - whitelists/gender
   * - Here you can see the non-abbreviated gender whitelist for comparison.
   * - 
      .. code-block:: yaml
          
          whitelist_type: plain
          whitelist:
            - male
            - female
            - mixed


A special case to be considered is when an experimental factor can take a dictionary as its value. In this case, not only the possible values for the keys within the dictionary, but also the key names themselves must be abbreviated.

**Example:**

.. list-table::
   :width: 100%
   :widths: 50

   * - Extract for disease from keys.yaml
   * - As shown in the extract from keys.yaml, the experimental factor disease is divided into the subdomains status, type, and stage using an underlying dictionary.
   * - 
       .. code-block:: yaml
          
          disease:
            ...
            value:
              disease_type:
                ...
              disease_status:
                ...
              disease_stage:
                ... 
            

.. list-table::
   :width: 100%
   :widths: 50

   * - whitelists/abbrev/disease
   * - Abbreviations must be created for the keys disease_status, disease_type and disease_stage which are included in disease, since these keys are also written in the file name.
   * - 
        .. code-block:: yaml
          
          whitelist_type: abbrev
          whitelist:
            disease_status: sts
            disease_type: tp
            disease_stage: stg


.. list-table::
   :width: 100%
   :widths: 50

   * - whitelists/abbrev/disease_status
       whitelists/abbrev/disease_type
   * - Here you can see the abbreviated whitelists for the values of the keys. For disease_stage no abbrev whitelist was created, because the included values are already very short and do not contain any special characters.
   * - **disease_status:**

        .. code-block:: yaml
          
          whitelist_type: abbrev
          whitelist:
            healthy: hlth
            recovered: rcvd
        
        **disease_type:**

        .. code-block:: yaml
          
          whitelist_type: abbrev
          whitelist:
            Lung cancer: LngCnc
            Asthma: Asth
            Pneumonia: pneum

Linking whitelists
-------------------

Linking to existing whitelists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to specifying possible values in the form of a list under the key 'whitelist', it is also possible to link to existing whitelist files. This is useful if the possible values of two different metadata fields are the same. In this case it is sufficient to create the values for only one of these fields and to link to the already created values in the whitelist of the other field. This way the values only have to be maintained in one place.
The following examples show how such a link can be built into various whitelists.

**Example 1 : plain**

This example shows what a link in a whitelist of type 'plain' can look like. Assume that a key setting_technique appears in the experimental setting section whereas a key technique is located in the technical details section. The former represents the measurement technique used for the respective experimental setting. The latter summarizes all measurement techniques used in the experiment. The possible techniques are the same in both fields.

.. list-table::
   :width: 100%
   :widths: 50

   * - Extract for technique from keys.yaml
   * - For this example it is assumed that under 'experimental_setting' a new key 'setting_technique' is added, which contains the measurement of the samples per experimental
       setting. All used techniques are then summarized again in a list under 'technical_details'.
   * - 
       .. code-block:: yaml
          
          experimental_setting:
            ...
            value:
                setting_technique:
                    mandatory: True
                    list: False
                    display_name: 'Technique'
                    desc: ''
                    value: null
                    whitelist: True
                    input_type: select
                technical_details:
                    ...
                    value:
                        technique:
                            mandatory: True
                            list: True
                            display_name: 'Technique'
                            desc: ''
                            value: null
                            whitelist: True
                            input_type: select

.. list-table::
   :width: 100%
   :widths: 50 50

   * - whitelists/technique
     - whitelists/setting_technique
   * - In the whitelist for technique all possible techniques for sample measurement are already defined.
     - For the whitelist 'setting_technique' the values can be adopted from the whitelist 'technique' by specifying its path under the key 'whitelist'. 
   * - 
        .. code-block:: yaml
          
          whitelist_type: plain
          whitelist:
          - bulk RNA-seq
          - bulk RNA array
          - bulk ATAC-seq
          - bulk ChIP-seq
          ...
     
     - 
        .. code-block:: yaml
          
          whitelist_type: plain
          whitelist: technique


**Example 2 : group**

This example shows how a link in a whitelist of type "group" can look like. For this we consider the whitelist of 'enrichment'.

.. list-table::
   :width: 100%
   :widths: 50 

   * - whitelists/enrichment
   * - The whitelist for enrichment is grouped into 'histone marks', 'proteins' and 'other'. The proteins correspond to the genes specified in the gene
       whitelist for each organism. By specifying the path to 'gene' whitelist, it can be linked under 'proteins', so that for this section the values
       from gene whitelist are adopted.
   * - 
       .. code-block:: yaml
          
          whitelist_type: group
          whitelist:
            histone marks:
            - H2BK12ac
            - H2BK20ac
            ...
            proteins: gene
            other:
            - dmR24
            - dmR24delta
            ...


.. list-table::
   :width: 100%
   :widths: 50 

   * - whitelists/gene
   * - The gene whitelist depends on the organism. This means that the 'proteins' part of the 'enrichment' whitelist is also dependent on the organism.
   * - 
        .. code-block:: yaml
          
          whitelist_type: depend
          ident_key: organism_name
          whitelist:
            human: genes/human
            mouse: genes/mouse
            zebrafish: genes/zebrafish
            rat: genes/rat
            pig: genes/pig
            medaka: genes/medaka
            chicken: genes/chicken
            drosophila: genes/drosophila
            yeast: genes/yeast


**Example 3 : depend**

Links can also be added for dependent whitelists. There are two ways to do this. Firstly, the paths to existing whitelists can be specified, as has already been done for 'plain' and 'group'. On the other hand, the keys under 'whitelist' can be omitted if the linked whitelist is named the same as the value it depends on. The following table shows both possibilities using the example of the whitelist for the key 'values'.

.. list-table::
   :width: 100%
   :widths: 40 60

   * - whitelists/factor
     - whitelists/values
   * - The whitelist for the experimental factors is displayed here for overview. The values in the whitelist for 'values' depend on the factor entered from this list.
     - The whitelist for values depends on the entered value under 'factor' and the possible values should correspond to the values of the selected factor. For this
       reason, for each key under 'whitelist', the corresponding whitelist of the experimental factor is linked.
   * - 
       .. code-block:: yaml
          
          whitelist_type: plain
          whitelist:
          - genotype
          - tissue
          - cell_type
          - knockdown
          - gender
          - life_stage
          - age
          - ethnicity
          - gene
          - disease
          - treatment
          - time_point
          - flow
          - enrichment
          - body_mass_index
          - injury

     - 
        .. code-block:: yaml
          
          whitelist_type: depend
          ident_key: factor
          whitelist:
            genotype: genotype
            tissue: tissue
            cell_type: cell_type
            knockdown: knockdown
            gender: gender
            life_stage: life_stage
            ethnicity: ethnicity
            gene: gene
            flow: flow
            enrichment: enrichment
      

.. list-table::
   :width: 100%
   :widths: 50

   * - whitelists/values
   * - Each key in column two under 'whitelist' represents an experimental factor. The linked whitelist files show that the respective whitelist is named the same as 
       the factor whose possible values it contains. For this reason, it is possible to omit the keys for the experimental factors, since the program automatically 
       searches for a whitelist with the same name as the key/experimental factor.
   * - 
        .. code-block:: yaml
          
          whitelist_type: depend
          ident_key: factor


Subdivide whitelists into smaller files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If whitelists are very long, it may make sense to split them into smaller whitelists. This is especially helpful if the files are in a dependent whitelist. This way a separate whitelist file can be created for each key under 'whitelist'. This speeds up reading and processing, because in this case not all whitelist values have to be imported, but only those that fulfill the dependency. The following example shows the splitting of the whitelists for the whitelist 'gene'.

**Example:**

.. list-table::
   :width: 100%
   :widths: 50

   * - whitelists/gene
   * - The whitelists for the genes per organism are very long, which is why they are outsourced to individual files. The keys are named 
       after the organisms and the path to the respective whitelist is given as value. 
   * - 
       .. code-block:: yaml
          
          whitelist_type: depend
          ident_key: organism
          whitelist:
            human_9606: genes/human
            mouse_10090: genes/mouse
            zebrafish_7955: genes/zebrafish
            ...


.. list-table::
   :width: 100%
   :widths: 50

   * - whitelists/genes/human
   * - For the whitelists per organism a new folder 'genes' was created. The whitelists are named after the organism for which they 
       contain the genes. The naming of the files does not follow any fixed rule but is subject to personal preference.
   * - 
        .. code-block:: yaml
          
          whitelist_type: plain
          ...
          whitelist:
          - TSPAN6_ENSG00000000003
          - TNMD_ENSG00000000005
          - DPM1_ENSG00000000419
          - SCYL3_ENSG00000000457
          - C1orf112_ENSG00000000460
          ...

