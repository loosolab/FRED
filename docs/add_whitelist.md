## Whitelist storage

The whitelists for the project are located in the git repository inside the 'whitelists' folder. All newly created whitelist files must also be placed in this folder so that the metadata tool can read them.

The naming of the whitelists is identical to the key for which it is created. For example, the whitelist for the key 'organism' is also named 'organism'. 

## Whitelist types

In the Project there are three different ways to file whitelists. The default is 'plain text', where the whitelist elements are listed one below the other in lines.
Another option is 'group', where the whitelist items can be divided into subgroups to improve clarity.
Finally, whitelists can be made dependent on input for other keys using the whitelist type 'depend'. This is useful e.g. for genes, which can be made dependent on the examined organism.

### Type 1: plain text

This type of whitelist is the simplest, as it contains all values in plain text format. One line of the text document corresponds to one value in the whitelist.

__Example: whitelists/gender__
```text
male
female
mixed
```

### Type 2: group

TBA

### Type 3: depend

This type of whitelist is used when the values depend on the input of another key in the metadata structure. 
The whitelist is organized here using a yaml file. Each whitelist of type 'depend' must contain the keys 'whitelist_type' and 'ident_key'.
The 'whitelist_type' is set with the value 'depend'. This identifies how the whitelist must be read within the metadata tool.
The key 'ident_key' names the key on whose input the whitelist should depend. For example, if you want to make the whitelist for genes dependent on the examined organism, you set the value for 'ident key' to 'organism'.

The possible elements of the 'ident_key' (the values in the whitelist for the 'ident_key' are then specified as further keys. For the 'ident_key' 'organism' possible keys would be 'human_9606', 'mouse_10090', 'zebrafish_7955' etc. For each of these keys the whitelist can be entered as a list.

__Example:__

<table style="width:80px;"">
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
The whitelist for the reference genome depends on the organism. For this reason, the 'ident_key' is assigned 'organism'. The organisms are the keys whose values are the whitelists.
</td> 
<td> 
The whitelist for 'organism' contains all allowed organisms as values. These form the keys in the dependent whitelist 'reference_genome'.
</td>
</tr>
<tr>
<td>

```yaml
whitelist_type: depend
ident_key: organism
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

```text
human_9606
mouse_10090
zebrafish_7955
...
```
</td>
</tr>
</table>


If the whitelists per key are very long, it makes sense to separate them into individual files. In this case the path to the whitelist within the folder 'whitelists' is specified as value instead of the whitelist itself. Since the path to the whitelist is specified explicitly, the naming of the whitelist can differ from the key and be chosen by the user. The whitelists can also be organized in subfolders.

__Example:__


<table style="width:100%">
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


<table style="width:100%">
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
