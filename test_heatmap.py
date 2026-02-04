from create_heatmap import *
import argparse
import pathlib
from jinja2 import Template
import fred.src.web_interface.html_output as ho

parser = argparse.ArgumentParser("Metadata Heatmap")
parser.add_argument(
    "-p",
    "--path",
    type=pathlib.Path,
    required=True,
    help="The path of the metadata file",
)

args = parser.parse_args()
input_file = utils.read_in_yaml(args.path)
key_yaml = utils.read_in_yaml("keys.yaml")

fig = get_heatmap(input_file, key_yaml, show_setting_id=False)


# fetch all filenames from the yaml via a generator -> nested lists
filename_nested = list(
    utils.find_list_key(input_file, "technical_replicates:filenames")
)
print(filename_nested)

# save filenames in html and string format
filenames = ho.get_html_filenames(filename_nested)
print(filenames)

input = {}
plot_list = []
for elem in fig:
    add_plot = {"header": elem[0]}
    if elem[1] is not None:
        add_plot["plot"] = (elem[1],)
    if elem[2] is not None:
        add_plot["missing_samples"] = ho.object_to_html(elem[2], 0, False)
    plot_list.append(add_plot)

for elem in ["project", "experimental_setting", "technical_details"]:
    header = elem.replace("_", " ").title()
    if elem == "experimental_setting":
        input["experimental_setting"] = {
            "header": "Experimental Setting",
            "plots": plot_list,
        }
    else:
        input[elem] = {
            "header": header,
            "html": ho.object_to_html(input_file[elem], 0, False),
        }

template = Template(
    """
        {% for key, value in input.items() %}
            {% if loop.index0 != 0 %}
                <hr/>
            {% endif %}
            <h3>{{ value.header }}</h3>
                        
            {% if value.html %}
                <div style="woverflow:auto; overflow-y:hidden; margin:0 auto; white-space:nowrap; padding-top:5">
                    {{ value.html }}
                </div>
            {% else %}
                            
                {% for elem in value.plots %}

                    {% if loop.index0 != 0 %}
                        <hr style="border-style: dotted;" />
                    {% endif %}
                                
                    <div style="woverflow:auto; overflow-y:hidden; margin:0 auto; white-space:nowrap; padding-top:5">
                        {{ elem.plot }}

                        {% if elem.missing_samples %}
                            <i>Conditions without samples:</i>
                            {{ elem.missing_samples }}
                        {% endif %}
                    </div>
                                
                {% endfor %} 

            {% endif %}
        {% endfor %}
                
        """
)

html_str = template.render(input=input)
# fig[1].show()

with open("Output.html", "w") as file:
    file.write(html_str)
