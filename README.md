# metadata organizer

https://loosolab.pages.gwdg.de/software/metadata-organizer/


# How to install

1. Clone the repository 
```
git clone git@gitlab.gwdg.de:loosolab/software/metadata-organizer.git
```
2. Move to the new repository directory
```
cd metadata-organizer
```
3. Create a pip environment
```
python3 -m venv .venv
```
4. Activate the environment
```
source .venv/bin/activate
```
5. Install the package
```
pip install .
```

# Create plots

```
fred plot -p PATH
```

optional parameters:

| --- | ---------- | ------------------------------------------------------------------------------------------------------ |
| -c  | --config   | path to configuration file in YAML format                                                              |
| -m  | --mode     | samples or conditions, default is samples                                                              |
| -s  | --setting  | int, index of experimental setting, default is 1                                                       |
| -l  | --labels   | factors, all or none, default is factors                                                               |
| -o  | --output   | show, png or html, default is show                                                                     |
| -f  | --filename | path including filename of the output file without file extension (e.g. output_folder/output_filename) |