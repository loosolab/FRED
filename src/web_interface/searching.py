import src.find_metafiles as find_metafiles
import src.utils as utils
import src.web_interface.html_output as html_output
import src.web_interface.wi_utils as wi_utils
import src.file_reading as file_reading

# TODO: refactor and comment


def get_meta_info(key_yaml, path, project_ids):
    """
    This file creates an HTML summary for a project containing metadata
    :param path: the path of a folder to be searched for a project
    :param project_id: the id of the project
    :return: html_str: the summary in HTML
    """

    for pr_id in project_ids:
        # TODO: own function
        # If file must be searched
        metafiles, validation_reports = file_reading.iterate_dir_metafiles(key_yaml,
            [path], return_false=True)
        correct_file = None
        for metafile in metafiles:
            if 'project' in metafile and 'id' in metafile['project'] and \
                    metafile['project']['id'] == pr_id:
                correct_file = metafile
                break

        if correct_file is not None:

            html_str = f'<h2 style="text-align:center;">{pr_id}</h2><hr>'
            if validation_reports['error_count'] > 0 or \
                    validation_reports['warning_count'] > 0:
                error = None
                warning = None

                for report in validation_reports['corrupt_files']['report']:
                    if report['file']['path'] == correct_file['path']:
                        error = report['error']
                        warning = report['warning']
                        break

                # TODO: error Handling + Ausgabe
                if error is not None:
                    html_str += f'<font color="red"><h3><b>ERROR:</b></h3>'
                    if len(error[0]) > 0:
                        html_str += f'<b>Missing mandatory keys:</b><br>'
                        html_str += '<ul>'
                        for elem in error[0]:
                            html_str += f'<li>{elem}</li>'
                        html_str += '</ul>'
                    if len(error[1]) > 0:
                        print(error[1])
                        html_str += f'<b>Invalid keys:</b><br>'
                        html_str += '<ul>'
                        for elem in error[1]:
                            value = correct_file
                            for key in elem.split(':'):
                                if isinstance(value, list):
                                    for l_elem in value:
                                       if key in l_elem:
                                           value = l_elem[key]
                                           break
                                else:
                                    value = value[key]
                            html_str += f'<li>{elem}: {value}</li>'
                            correct_file = wi_utils.pop_key(correct_file,
                                                            elem.split(':'), value)
                        html_str += '</ul>'

                    if len(error[2]) > 0:
                        html_str += f'<b>Invalid entries:</b><br>'
                        html_str += '<ul>'
                        for elem in error[2]:
                            html_str += f'<li>{elem.split(":")[-1]} in ' \
                                        f'{":".join(elem.split(":")[:-1])}</li>'
                            correct_file = wi_utils.pop_value(
                                correct_file, elem.split(":")[:-1],
                                elem.split(":")[-1])
                        html_str += '</ul>'

                    if len(error[3]) > 0:
                        html_str += f'<b>Invalid values:</b><br>'
                        html_str += '<ul>'
                        for elem in error[3]:
                            html_str += f'<li>{elem[0]}: {elem[1]} -> ' \
                                        f'{elem[2]}</li>'
                        html_str += '</ul>'

                    html_str += '</font><hr style="border-top: dotted 1px; background-color: transparent;" />'

                if warning is not None:
                    html_str += f'<font color="orange"><h3><b>WARNING:</b></h3>'
                    html_str += '<ul>'
                    for elem in warning:
                        message = elem[0].replace("\'", "")
                        html_str += f'<li>{message}: {elem[1]}</li>'
                    html_str += '</ul>'
                    html_str += '</font><hr style="border-top: dotted 1px; background-color: transparent;" />'

            if 'path' in correct_file:
                correct_file.pop('path')
            for elem in correct_file:
                end = f'{"<hr><br>" if elem != list(correct_file.keys())[-1] else ""}'
                html_str = f'{html_str}<h3>{elem}</h3>' \
                           f'{html_output.object_to_html(correct_file[elem], 0, False)}<br>'\
                           f'{end}'

        else:
            html_str = 'No metadata found.<br>'
    return html_str, correct_file


def get_search_mask(key_yaml):
    """
    This functions returns all necessary information for the search mask.
    :return: a dictionary containing all keys of the metadata structure and a
             whitelist object
    """
    keys = [
        {'key_name': 'All keys', 'display_name': 'All Fields', 'nested': [],
         'whitelist': False, 'chained_keys': ''}]
    keys += get_search_keys(key_yaml, '')
    return {'keys': keys}


def find_metadata(key_yaml, path, search_string):
    """
    This function searches for metadata files that match a search string in a
    given directory
    :param path: the path that should be searched
    :param search_string: the search string
    :return: new_files: a list containing all matching files
    """
    files = find_metafiles.find_projects(key_yaml, path, search_string, True)
    new_files = []
    for i in range(len(files)):
        for key in files[i]:
            res = {'id': key,
                   'path': files[i][key]['path']}
            try:
                res['project_name'] = files[i][key]['project']['project_name']
            except KeyError:
                res['project_name'] = None

            try:
                res['owner'] = files[i][key]['project']['owner']['name']
            except KeyError:
                res['owner'] = None

            try:
                res['email'] = files[i][key]['project']['owner']['email']
            except KeyError:
                res['email'] = None

            res['organisms'] = list(utils.find_keys(files[i][key], 'organism_name'))

            try:
                res['description'] = files[i][key]['project']['description']
            except KeyError:
                res['description'] = None

            try:
                res['date'] =  files[i][key]['project']['date']
            except KeyError:
                res['date'] = None

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
    This function returns all keys of the metadata structure in a nested way
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
                <= set(key_yaml[key]['value'].keys()) and not (
                'special_case' in key_yaml[key] and 'merge' in
                key_yaml[key]['special_case']):
            d['nested'] = get_search_keys(key_yaml[key]['value'],
                                          f'{chained}{key}:'
                                          if chained != '' else f'{key}:')
        else:
            d['chained_keys'] = f'{chained}{key}:' \
                if chained != '' else f'{key}:'
            d['nested'] = []

        if 'whitelist' in key_yaml[key]:
            d['whitelist'] = key_yaml[key]['whitelist']
        elif 'special_case' in key_yaml[key] and 'merge' in \
                key_yaml[key]['special_case']:
            d['whitelist'] = key_yaml[key]['value'][key_yaml[key][
                'special_case']['merge']]['whitelist']

        if 'whitelist' in d and d['whitelist']:
            d['search_info'] = {'key_name': key}
        res.append(d)
    return res
