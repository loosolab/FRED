import src.utils as utils
import src.web_interface.wi_object_to_yaml as oty
import copy

#TODO: inline comments


def get_summary(wi_object):
    """
    This function parses the wi object into a yaml structure and then parses
    the yaml to HTML to be output in the web interface. It also returns a list
    of filenames
    :param wi_object: the filled wi object
    :return: a dictionary containing the yaml structure as a dictionary and as
             HTML as well as the filenames as a string and in HTML
    """
    factors = copy.deepcopy(wi_object['all_factors'])
    new_object = {}
    for part in ['project', 'experimental_setting', 'technical_details']:
        new_object[part] = wi_object[part]
    new_object['all_factors'] = factors
    yaml_object = oty.parse_object(new_object)
    if 'project' in yaml_object and 'id' in yaml_object['project']:
        project_id = yaml_object['project']['id']
    else:
        project_id = None
    filename_nested = list(
        utils.find_list_key(yaml_object, 'technical_replicates:sample_name'))
    html_filenames, filenames = get_html_filenames(filename_nested)
    html_str = ''
    for elem in yaml_object:
        end = f'{"<hr><br>" if elem != list(yaml_object.keys())[-1] else ""}'
        html_str = f'{html_str}<h3>{elem}</h3>' \
                   f'{object_to_html(yaml_object[elem], 0, 0, False)}' \
                   f'<br>{end}'
    return {'yaml': yaml_object, 'summary': html_str,
            'file_names': html_filenames, 'file_string': (
                project_id,
                '\n'.join(filenames)) if project_id is not None else None}


def get_html_filenames(filename_nest):
    """
    This function parses the filenames into HTML
    :param filename_nest: a nested list of filenames
    :return:
    html_filenames: the file names in HTML format
    filenames: the filenames as a string
    """
    filenames = []
    html_filenames = ''
    for file_list in filename_nest:
        part_html = ''
        for filename in file_list:
            part_html = f'{part_html}- {filename}<br>'
            filenames.append(filename)
        end = f'{"<br><hr><br>" if file_list != filename_nest[-1] else "<br>"}'
        html_filenames = f'{html_filenames}{part_html}{end}'
    return html_filenames, filenames


def object_to_html(yaml_object, depth, margin, is_list):
    """
    This function parses the yaml structure into HTML
    :param yaml_object: a dictionary containing the yaml format
    :param depth: the depth of the indentation
    :param margin: the margin for the indentation
    :param is_list: a boolean to state if a key contains a list
    :return: html_str: the yaml structure in HTML
    """
    html_str = ''
    if isinstance(yaml_object, dict):
        for key in yaml_object:
            if key == list(yaml_object.keys())[0] and is_list:
                input_text = object_to_html(yaml_object[key],
                                            depth + 1, margin + 1.5, is_list)
                html_str = f'{html_str}<ul class="list-style-type-circle">' \
                           f'<li><p><font color={get_color(depth)}>{key}' \
                           f'</font>: {input_text}</p></li></ul>'
            else:
                input_text = object_to_html(yaml_object[key],
                                            depth + 1, margin + 1.5, is_list)
                html_str = f'{html_str}<ul class="list-style-none"><li><p>' \
                           f'<font color={get_color(depth)}>{key}</font>: ' \
                           f'{input_text}</p></li></ul>'
    elif isinstance(yaml_object, list):
        for elem in yaml_object:
            if not isinstance(elem, list) and not isinstance(elem, dict):
                html_str = f'{html_str}<ul class="list-style-type-circle">' \
                           f'<li><p>{elem}</p></li></ul>'
            else:
                html_str = f'{html_str}' \
                           f'{object_to_html(elem, depth, margin, True)}'
    else:
        html_str = f'{html_str}{yaml_object}'
    return html_str


def get_color(depth):
    """
    This function returns a color for the key in the HTML format depending on
    its indentation
    :param depth: the depth of indentation
    :return: color: the color in which the key should be colored
    """
    if depth % 2 == 0:
        color = '26a69a'
    else:
        color = '#d95965'
    return color
