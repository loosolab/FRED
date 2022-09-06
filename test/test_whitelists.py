#! /usr/bin/env python

import os
import sys
import collections
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import utils

def test_whitelists():
    whitelist_path = os.path.join(os.path.dirname(__file__), '..', 'whitelists')
    whitelist_files = [f for f in os.listdir(whitelist_path) if os.path.isfile(os.path.join(whitelist_path, f))]
    res = []
    for file in whitelist_files:
        res.append(test_whitelist(file, whitelist_path, None))
    if sum(filter(None, res)):
        sys.exit(1)
    else:
        sys.exit(0)


def test_whitelist(file, whitelist_path, depend):
    whitelist = utils.read_whitelist(file)
    headers = False
    if isinstance(whitelist, dict):
        if whitelist['whitelist_type'] == 'plain':
            if 'headers' in whitelist:
                headers = True
                duplicates = [elem for elem, count in
                              collections.Counter(whitelist['whitelist']).items() if
                              count > 1]
                if len(duplicates) > 0:
                    print(f'{file}: There are duplicates in the whitelist!')
                    return 1
                res = []
                for i in range(len(whitelist['headers'].split(' '))):
                    res.append(testing(whitelist['headers'].split(' ')[i], list(set([elem.split(' ')[i] for elem in whitelist['whitelist']])), whitelist_path, headers, depend))
                return sum(filter(None, res))
            else:
                return testing(file, whitelist['whitelist'], whitelist_path, headers, depend)
        elif whitelist['whitelist_type'] == 'group':
            whitelist = [x for xs in list(whitelist.values()) if xs is not None
                         for x in xs]
            return testing(file, whitelist, whitelist_path, headers, depend)
        elif whitelist['whitelist_type'] == 'depend':
            if whitelist['ident_key'] == 'organism_name':
                depend_elems = [x.split(' ')[0] for x in
                                utils.read_whitelist('organism')['whitelist']]
            else:
                depend_elems = utils.read_whitelist(whitelist['ident_key'])['whitelist']
            res = []
            for elem in depend_elems:
                if elem in whitelist:
                    whitelist2 = whitelist[elem]
                    if os.path.isfile(os.path.join(whitelist_path, whitelist2)):
                        res.append(test_whitelist(whitelist2, whitelist_path, elem))
                    else:
                        res.append(testing(elem, whitelist2, whitelist_path, headers, depend))
                else:
                    if os.path.isfile(os.path.join(whitelist_path, elem)):
                        res.append(test_whitelist(elem, whitelist_path, elem))
            return sum(filter(None, res))


def testing(file, whitelist, whitelist_path, headers, depend):
    duplicates = [elem for elem, count in
                      collections.Counter(whitelist).items() if count > 1]
    if len(duplicates) > 0:
        print(f'{file}: There are duplicates in the whitelist!')
        return 1
    if os.path.isfile(os.path.join(whitelist_path, 'abbrev', file)):
        abbrev = utils.read_whitelist(os.path.join('abbrev', file))
        if abbrev['whitelist_type'] == 'depend':
            if abbrev['ident_key'] == 'organism_name':
                depend_elems = [x.split(' ')[0] for x in
                                utils.read_whitelist('organism')['whitelist']]
            else:
                depend_elems = utils.read_whitelist(abbrev['ident_key'])
            res = []
            for elem in depend_elems:
                if depend is not None and elem == depend:
                    if elem in abbrev:
                        if os.path.isfile(os.path.join(whitelist_path, abbrev[elem])):
                            abbrev = utils.read_whitelist(os.path.join(whitelist_path, abbrev[elem]))
                        res.append(testing2(elem, whitelist, abbrev, headers))
            return sum(filter(None, res))


def testing2(file, whitelist, abbrev, headers):
    for i in range(len(whitelist)):
        if abbrev is not None and whitelist[i].lower() in abbrev:
            whitelist[i] = abbrev[whitelist[i].lower()]

    if not headers:
        duplicates = [elem for elem, count in
                  collections.Counter(whitelist).items() if count > 1]
        if len(duplicates) > 0:
            print(f'{file}: There are duplicates in the whitelist!')
            return 1
    for elem in whitelist:
        if any(symbol in elem for symbol in
               ['\'', '"', '_', '(', ')', '[', ']', '{', '}', '#', ',',
                ':', ';', '.', '+', '|', '*', '-', '<', '>', ' ']):
            print(f'{file}, {elem}: Invalid symbol!')
            return 2
    return 0


if __name__ == "__main__":
    test_whitelists()