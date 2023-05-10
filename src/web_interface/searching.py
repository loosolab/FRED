import src.find_metafiles as find_metafiles
import src.utils as utils
import src.web_interface.html_output as html_output
import src.web_interface.git_whitelists as git_whitelists
import os


def get_meta_info(path, project_id):
    """
    This file creates an HTML summary for a project containing metadata.
    :param path: the path of a folder to be searched for a project
    :param project_id: the id of the project
    :return: html_str: the summary in HTML
    """
    # If file must be searched

    yaml = find_metafiles.find_projects(path, f'id:{project_id}', True)
    if len(yaml) == 0:
        return f'No metadata found.'
    else:
        count = 0
        for elem in yaml:
            for key in elem:
                if key == project_id:
                    yaml = elem[key]
                    count += 1
        if count > 1:
            return f'Error: Multiple metadata files found.'
        else:
            if 'path' in yaml:
                yaml.pop('path')
            html_str = ''
            for elem in yaml:
                end = f'{"<hr><br>" if elem != list(yaml.keys())[-1] else ""}'
                html_str = f'{html_str}<h3>{elem}</h3>' \
                           f'{html_output.object_to_html(yaml[elem], 0, 0, False)}<br>' \
                           f'{end}'
            return html_str


def get_search_mask():
    """
    This functions returns all necessary information for the search mask.
    :return: a dictionary containing all keys of the metadata structure and a
             whitelist object
    """
    git_whitelists.get_whitelists()

    key_yaml = utils.read_in_yaml(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'keys.yaml'))
    keys = [
        {'key_name': 'All keys', 'display_name': 'All Fields', 'nested': [],
         'whitelist': False, 'chained_keys': ''}]
    keys += get_search_keys(key_yaml, '')
    return {'keys': keys}


def find_metadata(path, search_string):
    """
    This function searches for metadata files that match a search string in a
    given directory.
    :param path: the path that should be searched
    :param search_string: the search string
    :return: new_files: a list containing all matching files
    """
    files = find_metafiles.find_projects(path, search_string, True)
    new_files = []
    for i in range(len(files)):
        for key in files[i]:
            res = {'id': key,
                   'path': files[i][key]['path'],
                   'project_name': files[i][key]['project']['project_name'],
                   'owner': files[i][key]['project']['owner']['name'],
                   'email': files[i][key]['project']['owner']['email'],
                   'organisms': list(
                       utils.find_keys(files[i][key], 'organism_name')),
                   'description': files[i][key]['project']['description'],
                   'date': files[i][key]['project']['date']}
            if 'nerd' in files[i][key]['project']:
                nerds = []
                for nerd in files[i][key]['project']['nerd']:
                    nerds.append(nerd['name'])
                res['nerd'] = nerds
            else:
                res['nerd'] = None
            new_files.append(res)
    return new_files


def get_search_keys(key_yaml, chained):
    """
    This function returns all keys of the metadata structure in a nested way.
    :param key_yaml: the read in keys.yaml
    :param chained: the position of the key
    :return: res: a dictionary containing all metadata keys
    """
    res = []
    for key in key_yaml:
        d = {'key_name': key,
             'display_name': list(utils.find_keys(
                 key_yaml, key))[0]['display_name']}
        if isinstance(key_yaml[key]['value'], dict) and not \
                set(['mandatory', 'list', 'desc', 'display_name', 'value']) \
                <= set(key_yaml[key]['value'].keys()) and not ('special_case' in key_yaml[key] and 'merge' in key_yaml[key]['special_case']):
            d['nested'] = get_search_keys(key_yaml[key]['value'],
                                          f'{chained}{key}:'
                                          if chained != '' else f'{key}:')
        else:
            d['chained_keys'] = f'{chained}{key}:' \
                if chained != '' else f'{key}:'
            d['nested'] = []

        if 'whitelist' in key_yaml[key]:
            d['whitelist'] = key_yaml[key]['whitelist']
        elif 'special_case' in key_yaml[key] and 'merge' in key_yaml[key]['special_case']:
            d['whitelist'] = key_yaml[key]['value'][key_yaml[key]['special_case']['merge']]['whitelist']

        if 'whitelist' in d and d['whitelist']:
            d['search_info'] = {'key_name': key}
        res.append(d)
    return res