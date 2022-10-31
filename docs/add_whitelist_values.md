# Adding values to a whitelist

For this example, we will extend the whitelist for 'reference_genome' with the reference genomes for zebrafish (danrer10, danrer11). This whitelist is created as a whitelist of type 'group'. To show the extension of whitelists of different types, it is converted to a 'plain' and 'depend' format for this example as well.

### Step 1: Finding the whitelist file and opening it in the web editor

Go to the [whitelist folder](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/tree/main/whitelists) in the repository. There, look for the file whose name matches the key whose possible values you want to extend. In this example, this is the file named 'reference_genome'.

![](images/whitelist_selection.png)

Open this file. Inside Github you will see a blue button 'Open in Web IDE' in the upper right corner. 

![](images/web-ide.png)

Clicking on it will open an editor where you can edit the selected whitelist.

### Step 2: Adding new values to the file

In the following table, the whitelist for 'reference_genome' is shown and expanded for each of the formats 'plain', 'group' and 'depend'.

<table>
<tr>
<th>
plain
</th>
<th>
group
</th>
<th>
depend
</th>
</tr>
<tr>
<td> 
<div>

The following snippet shows<br> 
the whitelist file for <br>
'reference_genome' in type <br>
'plain'.

```yaml
whitelist_type: plain
whitelist:
  - hg38
  - hg19
  - mm10
  - mm9
  - mm38
```

To add the reference genomes <br>
'danrer10' and 'danrer11' to a <br>
whitelist of type 'plain', they <br>
are inserted into the list under<br>
the key "whitelist":

```yaml
whitelist_type: plain
whitelist:
  - hg38
  - hg19
  - mm10
  - mm9
  - mm38
  - danrer10
  - danrer11
```

</div>
</td> 
<td> 
<div>

The following snippet shows the whitelist<br>
file for 'reference_genome' in type 'group'.

```yaml
whitelist_type: group
whitelist:
    human:
      - hg38
      - hg19
    mouse:
      - mm10
      - mm9
      - mm38
```

In the 'group' type whitelist, the specified<br> 
reference genomes are grouped according to <br>
the organism to which they are assigned. To <br>
add the reference genomes 'danrer10' and <br>
'danrer11' of the organism zebrafish in a <br>
meaningful way, we create the new category <br>
'zebrafish' as a key within the dictionary <br>
under 'whitelist'. This key 'zebrafish' then<br> 
gets ' danrer10' and 'danrer11' in a list as<br> 
value.

```yaml
whitelist_type: group
whitelist:
    human:
      - hg38
      - hg19
    mouse:
      - mm10
      - mm9
      - mm38
  zebrafish:
      - danrer10
      - danrer11
```

</div>
</td>
<td> 
<div>

The following snippet shows the whitelist<br>
file for 'reference_genome' in type 'depend'.

```yaml
whitelist_type: depend
ident_key: organism_name
whitelist:
    human:
      - hg38
      - hg19
    mouse:
      - mm10
      - mm9
      - mm38
```

The whitelist of type 'depend' is dependent <br>
on the input of another metadata field. The <br>
'ident_key' indicates that this metadata <br>
field is the 'organism_name' in our example.<br> 
This means that different whitelist values <br>
can be entered for the reference genome <br>
depending on the specified organism. Now, <br>
to add the reference genomes 'danrer10' and<br> 
'danrer11', we first have to decide for <br>
which organism our reference genomes are <br>
valid. For this we look at the possible <br>
organisms in the [whitelist 'organism'](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/blob/main/whitelists/organism):

```yaml
whitelist_type: plain
headers: organism_name taxonomy_id
whitelist:
    - human 9606
    - mouse 10090
    - zebrafish 7955
    - rat 10114
    - pig 9823
    - medaka 8090
    - chicken 9031
    - drosophila 7215
    - yeast 4932
```

In this whitelist we find an entry for <br>
zebrafish. From the header we see that the <br>
entry is composed of the 'organism_name' and<br>
the 'taxonomy_id'. So for the entry <br>
'zebrafish 7955' we get the 'organism_name' <br>
'zebrafish'. We now enter this as a key in <br>
the dictionary under 'whitelist' in our <br>
'reference_genome' whitelist. Note that the <br>
syntax of the key must match the <br>
'organism_name' specified in the 'organism' <br>
whitelist. Then, this new key 'zebrafish' <br>
receives a list containing the reference <br>
genomes 'danrer10' and 'danrer11' as value.

```yaml
whitelist_type: depend
ident_key: organism_name
whitelist:
    human:
      - hg38
      - hg19
    mouse:
      - mm10
      - mm9
      - mm38
    zebrafish:
      - danrer10
      - danrer11
```

</div>
</td>
</tr>
</table>
