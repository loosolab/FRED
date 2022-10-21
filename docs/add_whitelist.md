## Whitelist storage

The whitelists for the project are located in the git repository inside the 'whitelists' folder. All newly created whitelist files must also be placed in this folder so that the metadata tool can read them.

The naming of the whitelists is identical to the key for which it is created. For example, the whitelist for the key 'organism' is also named 'organism'. 

The whitelist files have the format yaml. For each whitelist two mandatory keys must be specified. The first one is 'whitelist_type' and describes the nature of the whitelist and how it must be processed in the program. There are four different whitelist types, which are described in more detail in the sections below.
The second mandatory key is called 'whitelist' and contains the values that can be accepted by the metadata field for which the whitelist was created.

## Whitelist types

### Type 1: plain

Whitelists of type plain are the simplest way to set values for a metadata field. A simple list of potential values is specified for the key whitelist. 

__Example:__

<table>
<tr>
<th>
whitelists/gender
</th>
</tr>
<tr>
<td>

```yaml
whitelist_type: plain
whitelist:
  - male
  - female
  - mixed
```

</td>
</tr>
</table>

### Type 2: group

This whitelist type is used to group the values within the whitelist for better organization. Here, the key whitelist receives a dictionary as value, whose keys represent subheadings. For these keys, thematically matching values are then stored in a list. When generating the metadata, the whitelist values are output in the same grouping as defined in the whitelist file. The aim of this whitelist type is to improve the clarity when creating and extending the whitelists as well as when generating the metadata file.

__Example:__

<table>
<tr>
<th>
whitelists/disease_type
</th>
</tr>
<tr>
<td> 
<div>
The whitelist values for 'disease_type' were grouped based on the organs affected by the disease.<br>
This allows faster finding of diseases in the list, as well as a better overview.
</div>
</td> 
</tr>
<tr>
<td>

```yaml
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
```

</td>
</tr>
</table>



### Type 3: depend

This type of whitelist is used when the values depend on the input of another key in the metadata structure. Each whitelist file of type depend contains beside 'whitelist_type' and 'whitelist' the further mandatory key 'ident_key'. This identifies the key in the metadata structure on whose input the whitelist should depend. For example, if you want to make the whitelist for genes dependent on the organism under investigation, set the value for 'ident_key' to 'organism_name'.
The key 'whitelist' receives a dictionary whose keys represent the possible values of the metadata field specified in 'ident_key'. These keys are then assigned the values in a list, which an input can accept depending on this key.

__Example:__

<table>
<tr>
<th>
whitelists/reference_genome
</th>
<th>
whitelists/organism
</th>
</tr>
<tr>
<td> 
<div>
In this example, the whitelist for the reference<br>
genome is represented as depending on the<br> 
organism.For this reason, the 'ident_key' is<br> 
assigned 'organism_name'. The possible organisms<br> 
form the keys specified under 'whitelist'. Their<br>
values are those reference genomes that can be<br> 
set for the respective organism.
</div>
</td> 
<td> 
<div>
The whitelist for 'organism_name' contains<br> 
all allowed organisms as values. These form<br> 
the keys in the dependent whitelist<br> 
'reference_genome'.
</div>
</td>
</tr>
<tr>
<td>

```yaml
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
```

</td>
<td>

```yaml
whitelist_type: plain
whitelist:
  - human_9606
  - mouse_10090
  - zebrafish_7955
  ...
```
</td>
</tr>
</table>

### Type 4: abbrev

This type of whitelist must be provided for all experimental factors, their values, and for the organisms. The fields mentioned are those from which file names for samples are generated during metadata creation. Since file names are limited in length, the values must be shortened using the abbrev whitelist. In this process, all special characters are also removed from the values.
Whitelists of type abbrev are located inside the 'whitelists' folder in the 'abbrev' folder. They are named after the key for whose values they contain the abbreviations.  
Here a dictionary is passed to the key 'whitelist'. The keys of this dictionary correspond to the values of the non-abbreviated whitelist. Each key receives its abbreviated version.

__Example:__

<table>
<tr>
<th>
whitelists/abbrev/gender
</th>
<th>
whitelists/organism
</th>
</tr>
<tr>
<td> 
<div>
In this example, the abbrev whitelist was<br> 
created for the experimental factor gender.
</div>
</td> 
<td> 
<div>
Here you can see the non-abbreviated gender<br> 
whitelist for comparison.
</div>
</td>
</tr>
<tr>
<td>

```yaml
whitelist_type: abbrev
whitelist:
  male: m
  female: f
  mixed: x
```

</td>
<td>

```yaml
whitelist_type: plain
whitelist:
  - male
  - female
  - mixed
```

</td>
</tr>
</table>

A special case to be considered is when an experimental factor can take a dictionary as its value. In this case, not only the possible values for the keys within the dictionary, but also the key names themselves must be abbreviated.

__Example:__

<table>
<tr>
<th>
Extract for disease from keys.yaml
</th>
<th>
whitelists/abbrev/disease
</th>
<th>
whitelists/abbrev/disease_status<br>
whitelists/abbrev/disease_type<br>
whitelists/abbrev/disease_stage
</th>
</tr>
<tr>
<td> 
<div>
TBA
</div>
</td> 
<td> 
<div>
TBA
</div>
</td>
<td> 
<div>
TBA
</div>
</td>
</tr>
<tr>
<td>

```yaml
whitelist_type: abbrev
whitelist:
  male: m
  female: f
  mixed: x
```

</td>
<td>

```yaml
whitelist_type: plain
whitelist:
  - male
  - female
  - mixed
```

</td>
<td>

```yaml
whitelist_type: plain
whitelist:
  - male
  - female
  - mixed
```

</td>
</tr>
</table>


## 

If the whitelists per key are very long, it makes sense to separate them into individual files. In this case the path to the whitelist within the folder 'whitelists' is specified as value instead of the whitelist itself. Since the path to the whitelist is specified explicitly, the naming of the whitelist can differ from the key and be chosen by the user. The whitelists can also be organized in subfolders.

__Example:__


<table>
<tr>
<td> 
<b>whitelists/gene</b><br>The whitelists for the genes per organism are very long, which is why they are outsourced to individual files. The keys are named after the organisms and the path to the respective whitelist is given as value. 
</td> 
<td> 
<b>whitelists/genes/human</b><br>For the whitelists per organism a new folder 'genes' was created. The whitelists are named after the organism for which they contain the genes. The naming of the files does not follow any fixed rule but is subject to personal preference. 
</td>
</tr>
<tr>
<td>

```yaml
whitelist_type: depend
ident_key: organism
human_9606: genes/human
mouse_10090: genes/mouse
zebrafish_7955: genes/zebrafish
...
```

</td>
<td>

```text
TSPAN6_ENSG00000000003
TNMD_ENSG00000000005
DPM1_ENSG00000000419
SCYL3_ENSG00000000457
C1orf112_ENSG00000000460
...
```
</td>
</tr>
</table>

If independent whitelist files already exist for the keys and the files are located in the folder whitelists and named exatly like the respective key, those keys can be omitted and the metadata tool reads the existing files as whitelist. This is e.g. the case for the whitelist 'values'. The key 'values' in the metadata structure contains the examined values of the examined experimental factor. So the whitelist for 'values' depends on the whitelist 'factor'. Since each experimental factor has its own whitelist, the keys for the experimental factors in the whitelist for 'value' can be omitted. Thus, the existing files are read in as whitelist.

__Example:__


<table>
<tr>
<td> 
<b>whitelists/values</b><br>The whitelist for values depends on the entered 'factor'. The value 'factor' is therefore assigned to the 'ident_key'.
</td> 
<td> 
<b>whitelists/factor</b><br>The key 'factor' also has a whitelist. All values specified in the whitelist 'factor' form possible keys in the whitelist 'values'.
</td>
<td> 
<b>whitelists/genotype</b><br>For the values in the whitelist 'factor' (e.g. genotype) there are separate whitelists named after the respective value. The values therefore no longer have to be specified as keys in the whitelist 'values'. The metadata tool reads the already existing files as whitelist.
</td> 
</tr>
<tr>
<td>

```yaml
whitelist_type: depend
ident_key: factor
```

</td>
<td>

```text
genotype
tissue
cell_type
knockdown
gender
...
```
</td>

<td>

```text
Mut
WT
```
</td>
</tr>
</table>


# Adding values to a whitelist

The whitelists are located in the git repository in the folder whitelists. The whitelist file is named after the key in the metadata structure for which a whitelist should be available. 

To add a value to an existing whitelist, search the whitelist folder for the desired whitelist named after the key and open it.
If the opened whitelist is of type 1, add the new value in a new line.

# Adding a new whitelist
