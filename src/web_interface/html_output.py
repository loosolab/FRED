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
    
    html_str = create_heatmap.get_heatmap(yaml_object, key_yaml)
    
    '''for elem in yaml_object:
        if elem == 'experimental_setting':
            end = f'{"<hr><br>" if elem != list(yaml_object.keys())[-1] else ""}'
            plots = create_heatmap.get_heatmap(yaml_object, key_yaml)
            html_str = f'{html_str}<h3>{elem}<h3>'
            for plot in plots:
                html_str = f'{html_str}{plot}<br>'
            html_str = f'{html_str}{end}'
        else:
            end = f'{"<hr><br>" if elem != list(yaml_object.keys())[-1] else ""}'
            html_str = f'{html_str}<h3>{elem}</h3>' \
                    f'{object_to_html(yaml_object[elem], 0, False)}' \
                    f'<br>{end}'
'''
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

    # yaml is a dictionary
    if isinstance(yaml_object, dict):

        # iterate over keys in dictionary
        for key in yaml_object:

            # first key in a list -> bullet point
            if key == list(yaml_object.keys())[0] and is_list:

                # convert value of key to html
                input_text = object_to_html(yaml_object[key], depth + 1,
                                            is_list)

                # call function get_color to select the color of the key and
                # add key and html value to html string with a bullet point
                html_str = f'{html_str}<ul class="list-style-type-circle">' \
                           f'<li><p><font color={get_color(depth)}>{key}' \
                           f'</font>: {input_text}</p></li></ul>'

            # key without bullet point
            else:

                # convert value of key to html
                input_text = object_to_html(yaml_object[key], depth + 1,
                                            is_list)

                # call function get_color to select the color of the key and
                # add key and html value to html string
                html_str = f'{html_str}<ul class="list-style-none"><li><p>' \
                           f'<font color={get_color(depth)}>{key}</font>: ' \
                           f'{input_text}</p></li></ul>'

    # yaml is a list
    elif isinstance(yaml_object, list):

        # iterate over list elements
        for elem in yaml_object:

            # list element is single value
            if not isinstance(elem, list) and not isinstance(elem, dict):

                # add value to html string with a bullet point
                html_str = f'{html_str}<ul class="list-style-type-circle">' \
                           f'<li><p>{elem}</p></li></ul>'

            # list element is dict or list
            else:

                # call this function on list element and add it to html string
                html_str = f'{html_str}{object_to_html(elem, depth, True)}'

    # yaml is a single value
    else:

        # add value to html string
        html_str = f'{html_str}{yaml_object}'

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
