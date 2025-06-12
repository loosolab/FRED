import src.utils as utils
import src.web_interface.wi_object_to_yaml as oty
import create_heatmap
from jinja2 import Template
import os
import plotly.graph_objects as go
import plotly.io as pio
import plotly as plt


def get_summary(wi_object, key_yaml, read_in_whitelists):
    """
    This function parses the wi object into a yaml structure and then parses
    the yaml to HTML to be output in the web interface. It also returns a list
    of filenames
    :param key_yaml: the read in general structure
    :param wi_object: the filled wi object
    :return: a dictionary containing the yaml structure as a dictionary and as
             HTML as well as the filenames as a string and in HTML
    """

    # parse wi_object to yaml
    yaml_object = oty.parse_object(wi_object, key_yaml, read_in_whitelists)
    
    # save the project_id from the yaml file
    if 'project' in yaml_object and 'id' in yaml_object['project']:
        project_id = yaml_object['project']['id']
    else:
        project_id = None

    # fetch all filenames from the yaml via a generator -> nested lists
    filename_nested = list(utils.find_list_key(
        yaml_object, 'technical_replicates:sample_name'))

    # save filenames in html and string format
    html_filenames, filenames = get_html_filenames(filename_nested)

    # rewrite yaml to html
    
    plots = create_heatmap.get_heatmap(yaml_object, key_yaml)

    input = {}
    for elem in yaml_object:
        header =  elem.replace("_", " ").title()
        if elem == 'experimental_setting':
            plots = create_heatmap.get_heatmap(yaml_object, key_yaml)
            plot_list = []
            for plot in plots:
                plot_list.append({'plot': plot[0], 'table': plot[1]})
            input[elem] = {'header': header, 'plots': plot_list}
        else:
            input[elem] = {'header': header, 'html': get_html_object(yaml_object[elem])}

            

    html_str = ''
    template = Template(
        '''
        {% for key, value in input.items() %}
            {% if loop.index0 != 0 %}
                <hr/>
            {% endif %}
            <h3>{{ value.header }}</h3>
                        
            {% if value.html %}
                {{ value.html }}
            {% else %}
                            
                {% for elem in value.plots %}

                    {% if loop.index0 != 0 %}
                        <hr style="border-style: dotted;" />
                    {% endif %}
                                
                    <div style="overflow:auto; overflow-y:hidden; margin:0 auto; white-space:nowrap; padding-top:20">
                        {{ elem.plot }}
                        {{ elem.table }}
                    </div>
                                
                {% endfor %} 
            {% endif %}
        {% endfor %}
        '''
        )
   
    html_str =  template.render(input=input)

    return {'summary': html_str, 'file_names': html_filenames,
            'file_string': (project_id, '\n'.join(filenames)) if
            project_id is not None else None}


def get_html_filenames(filename_nest):
    """
    This function parses the filenames into HTML
    :param filename_nest: a nested list of filenames
    :return:
    html_filenames: the file names in HTML format
    filenames: the filenames as a list of strings
    """

    # define empty list to store filenames in string format
    filenames = []

    # initialize html string
    html_filenames = ''

    # iterate over nested filenames
    for file_list in filename_nest:

        # initialize partial html string
        part_html = ''

        # iterate over single filenames
        for filename in file_list:

            # add the filename to the html and to the list
            part_html = f'{part_html}- {filename}<br>'
            filenames.append(filename)

        # add a break between the filenames and a horizontal line after the
        # last filename of the list
        end = f'{"<br><hr><br>" if file_list != filename_nest[-1] else "<br>"}'

        # add the converted file list to the html string
        html_filenames = f'{html_filenames}{part_html}{end}'

    return html_filenames, filenames


def get_html_object(yaml_object):
    html_str = '<table border-collapse: collapse;>'
    for key in yaml_object:
        html_str += f'<tr><td max-width: 200px; style="vertical-align: top; padding-right: 30px; padding-bottom: 10px; border-bottom: 1px solid #ddd; border-collapse: collapse;">{key}</td><td style="max-width: 1000px; vertical-align: top; padding-bottom: 10px; border-bottom: 1px solid #ddd; border-collapse: collapse;">{object_to_html(yaml_object[key], 0, False)}</td></tr>'
    html_str += '</table>'
    return html_str

def object_to_html(yaml_object, depth, is_list):
    """
    This function parses the yaml structure into HTML
    :param yaml_object: a dictionary containing the yaml format
    :param depth: the depth of the indentation
    :param is_list: a boolean to state if a key contains a list
    :return: html_str: the yaml structure in HTML
    """

    # initialize html string
    html_str = ''
    table_style = 'style="max-width: 150px; text-align: left; vertical-align: top; padding: 10px; border: 1px solid black; border-collapse: collapse;"'
    # yaml is a dictionary
    if isinstance(yaml_object, dict):

        if depth==0:
            keys = list(yaml_object.keys())

            html_str += '<table style="border: 1px solid black; border-collapse: collapse;">'
            html_str += f'<tr><th {table_style}>{("</th><th "+table_style+">").join(keys)}</th></tr>'

            vals = []
            for key in keys:
                vals.append(object_to_html(yaml_object[key], depth+1, False))
            html_str += f'<tr><td {table_style}>{("</td><td "+table_style+">").join(vals)}</td></tr>'
            html_str += '</table>'
        else:
            for key in yaml_object:
                html_str += f'<p>{key}: {object_to_html(yaml_object[key], depth+1, False)}</p>'
            pass
    
    elif isinstance(yaml_object, list):

        if depth == 0 and all([isinstance(x, dict) for x in yaml_object]):
            key_list = []
            for elem in yaml_object:
                for key in elem:
                    if key not in key_list:
                        key_list.append(key)
            html_str += '<table style="border: 1px solid black; border-collapse: collapse;">'
            html_str += f'<tr><th {table_style}>{("</th><th "+table_style+">").join(key_list)}</th></tr>'

            for elem in yaml_object:
                print(elem)
                vals = []
                for key in key_list:
                    if key in elem:
                        vals.append(object_to_html(elem[key], depth+1, False))
                    else:
                        vals.append('')
                html_str += f'<tr><td {table_style}>{("</td><td "+table_style+">").join(vals)}</td></tr>'
            html_str += '</table>'
        else:
            for elem in yaml_object:
                html_str += f'<p>- {object_to_html(elem, depth, False)}</p>'
    
    else:
        html_str += str(yaml_object)

    return html_str


# TODO: new color scheme -> 2 colors as parameter
def get_color(depth):
    """
    This function returns a color for the key in the HTML format depending on
    its indentation
    :param depth: the depth of indentation
    :return: color: the color in which the key should be colored
    """

    # color 1 if number of indentations is even
    if depth % 2 == 0:
        color = '26a69a'

    # color 2 if number of indentations is uneven
    else:
        color = '#d95965'

    return color
