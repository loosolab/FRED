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

The following snippet <br>
shows the whitelist file <br>
for 'reference_genome' in<br> 
type 'plain'.

```yaml
whitelist_type: plain
whitelist:
  - hg38
  - hg19
  - mm10
  - mm9
  - mm38
```

To add the reference <br>
genomes 'danrer10' and <br>
'danrer11' to a whitelist<br> 
of type 'plain', they are<br> 
inserted into the list <br>
under key "whitelist":

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

The following snippet <br>
shows the whitelist file <br>
for 'reference_genome' in<br> 
type 'group'.

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

In the 'group' type <br>
whitelist, the specified<br> 
reference genomes are <br>
grouped according to the <br>
organism to which they <br>
are assigned. To add the <br>
reference genomes <br>   
'danrer10' and 'danrer11'<br> 
of the organism zebrafish<br> 
in a meaningful way, we <br>
create the new category <br>
'zebrafish' as a key <br>
within the dictionary <br>
under 'whitelist'. This <br>
key 'zebrafish' then gets<br> 
'danrer10' and 'danrer11'<br> 
in a list as value.

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
<td markdown="1"> 

The following snippet <br>
shows the whitelist file <br>
for 'reference_genome' in<br> 
type 'depend'.

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

The whitelist of type <br>
'depend' is dependent on <br>
the input of another <br>
metadata field. The <br> 
'ident_key' indicates <br>
that this metadata field <br>
is the 'organism_name' in<br> 
our example. This means <br>
that different whitelist <br>
values can be entered for<br> 
the reference genome <br>
depending on the <br>    
specified organism. Now, <br>
to add the reference <br>
genomes 'danrer10' and <br>
'danrer11', we first have<br> 
to decide for which <br> 
organism our reference <br>
genomes are valid. For <br>
this we look at the <br> 
possible organisms in the<br>
 whitelist '[organism](https://gitlab.gwdg.de/loosolab/software/metadata-organizer/-/blob/main/whitelists/organism)':

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

In this whitelist we find<br>
an entry for zebrafish. <br>
From the header we see <br>
that the entry is <br>   
composed of the <br>     
'organism_name' and the <br>
'taxonomy_id'. So for the<br> 
entry 'zebrafish 7955' we<br> 
get the 'organism_name' <br>
'zebrafish'. We now enter<br> 
this as a key in the <br>
dictionary under <br>    
'whitelist' in our <br>  
'reference_genome' <br>  
whitelist. Note that the <br>
syntax of the key must <br>
match the 'organism_name'<br> 
specified in the <br>    
'organism' whitelist. <br>
Then, this new key <br>
'zebrafish' receives a <br>
list containing the <br>
reference genomes <br>
'danrer10' and 'danrer11'<br> 
as value.

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

</td>
</tr>
</table>
