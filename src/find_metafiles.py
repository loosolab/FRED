# 'project:id:pul47 and not project:owner:name:Jasmin Walter or project:id:pul50'
# -> [['project:id:pul47:True', 'project:owner:name:Jasmin Walter:False'],['project:id:pul50:True']]
def find_projects(metafiles_list, search_parameters):
    matches = []
    for metafile in metafiles_list:
        or_found = []
        print('searching file ' + metafile['path'])
        for or_param in search_parameters:
            and_found=[]
            for and_param in or_param:
                params = and_param.split(':')
                should_be_found=params[-1]
                match = find_entry(metafile, params[0:-2], params[-2])
                if (match and should_be_found == 'True') or \
                        (not match and should_be_found == 'False'):
                    and_found.append(True)
                else:
                    and_found.append(False)
            if False not in and_found:
                or_found.append(True)
        if True in or_found:
            matches.append(metafile['project']['id'])
    return matches


def find_entry(metafile, targets, target_value):
    try:
        if len(targets) > 1:
            if isinstance(metafile[targets[0]], list):
                for item in metafile[targets[0]]:
                    if find_entry(item, targets[1:], target_value):
                        return True
            else:
                return find_entry(metafile[targets[0]], targets[1:], target_value)
        else:
            if isinstance(metafile[targets[0]], list):
                if target_value in metafile[targets[0]]:
                    return True
            else:
                if metafile[targets[0]] == target_value:
                    return True
    except KeyError as e:
        print(e)