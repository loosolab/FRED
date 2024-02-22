import pytz
from dateutil import parser


def pop_key(metafile, key_list, value):
    """
    This function iterates over a list of keys in order to remove the last key
    and every key above it if its remaining value is an empty list or
    dictionary
    :param metafile: the read in metadata file
    :param key_list: a list of keys
    :param value: the value within the last key
    :return: metafile: the read in metadata file without the popped key
    """

    # metafile is a list
    if isinstance(metafile, list):

        # iterate over list
        for i in range(len(metafile)):

            # call this function on every list element
            metafile[i] = pop_key(metafile[i], key_list, value)

            # if the remaining list element is an empty dictionary or list then
            # set it to None
            if (isinstance(metafile[i], dict) or
                    isinstance(metafile[i], list)) and len(metafile[i]) == 0:
                metafile[i] = None

        # remove all list elements that are None
        metafile = [x for x in metafile if x is not None]

    # metafile is a dictionary
    elif isinstance(metafile, dict):

        # only one list key is left -> must be removed
        if len(key_list) == 1:

            # test if the key is in the metafile and its value matches the key
            # to be removed
            if key_list[0] in metafile and metafile[key_list[0]] == value:

                # remove the key from the metafile
                metafile.pop(key_list[0])

        # more keys are left in the list
        else:

            # call this function on the part of the metafile within the first
            # key of the list
            metafile[key_list[0]] = pop_key(metafile[key_list[0]],
                                            key_list[1:], value)
            # test if the remaining part of the metafile is an empty dictionary
            # or list
            if (isinstance(metafile[key_list[0]], dict) or
                    isinstance(metafile[key_list[0]], list)) and \
                    len(metafile[key_list[0]]) == 0:

                # remove the key from the metafile
                metafile.pop(key_list[0])

    return metafile


def pop_value(metafile, key_list, value):
    """
    This function removes a value from the metadata object. If the removal
    leads to an empty key or list then those are removed as well
    :param metafile: the read in metadata file
    :param key_list: a list of keys
    :param value: the value to be removed
    :return: metafile: the read in metadata file without the removed value
    """

    # only one key is in the list
    if len(key_list) == 1:

        # metafile is a list
        if isinstance(metafile, list):

            # iterate over the elements of the list
            for i in range(len(metafile)):

                # call this function on every list element
                metafile[i] = pop_value(metafile[i], key_list, value)

                # test if the remaining element is an empty dictionary or list
                if (isinstance(metafile[i], dict) or
                        isinstance(metafile[i], list)) and \
                        len(metafile[i]) == 0:

                    # set the element to None
                    metafile[i] = None

            # remove all list elements that are None
            metafile = [x for x in metafile if x is not None]

        # metafile is a dictionary and contains the key
        elif key_list[0] in metafile:

            # the value of the key is a list
            if isinstance(metafile[key_list[0]], list):

                # remove the faulty value from the list
                metafile[key_list[0]] = [x for x in metafile[key_list[0]] if
                                         x != value]

                # test if the remaining list is empty then remove the key
                if len(metafile[key_list[0]]) == 0:
                    metafile.pop(key_list[0])

            # remove the key if it contains the faulty value
            elif metafile[key_list[0]] == value:
                metafile.pop(key_list[0])

    # multiple keys in the list
    else:

        # metafile is a list
        if isinstance(metafile, list):

            # iterate over the list elements
            for i in range(len(metafile)):

                # call this function on every list element
                metafile[i] = pop_value(metafile[i], key_list, value)

                # set the element to None if it contains an empty list or
                # dictionary
                if len(metafile[i]) == 0:
                    metafile[i] = None

            # remove all elements from the list that are None
            metafile = [x for x in metafile if x is not None]

        # metafile is a dictionary
        elif isinstance(metafile, dict) and key_list[0] in metafile:

            # call this function on the part of the metafile within the first
            # key of the list
            metafile[key_list[0]] = pop_value(metafile[key_list[0]],
                                              key_list[1:], value)
            # test if the remaining part of the metafile is an empty dictionary
            # or list
            if (isinstance(metafile[key_list[0]], dict) or
                    isinstance(metafile[key_list[0]], list)) and \
                    len(metafile[key_list[0]]) == 0:

                # remove the key from the metafile
                metafile.pop(key_list[0])

    return metafile


def date_to_str(date):
    """
    This function converts the date from default time in ISO 8601 format to
    time zone Berlin and changes the format to 'DD.MM.YYYY'
    :param date: the date to be converted
    :return: the converted date
    """

    # read in the date as default time
    default_time = parser.parse(date)

    # initialize the time zone for Berlin
    timezone = pytz.timezone("Europe/Berlin")

    # convert the default time to the timezone Berlin
    local_time = default_time.astimezone(timezone)

    # return the date in the format 'DD.MM.YYYY'
    return local_time.strftime("%d.%m.%Y")


def str_to_date(value):
    """
    This function converts a string containing the date in the format
    'DD.MM.YYYY' to ISO 8601 format and changes the timezone from Berlin to
    default time
    :param value: the string value containing the date
    :return: the date in ISO 8601 format
    """

    # read in the string as local time
    local_time = parser.parse(value, dayfirst=True)

    # convert the local time to default time
    default_time = local_time.astimezone(pytz.utc)

    # return the date in the format ISO 8601
    return default_time.strftime("%Y-%m-%dT%X.%fZ")


def parse_headers(headers, value, mode='dict'):
    """
    This function splits a value into a dictionary depending on the header
    :param mode: a string defining the type the split value should be returned
                 as, default is 'dict'
                 -> dict: returns the split value in a dictionary
                 -> str: returns the split value as a string
                         ('<key1>:<value1>|<keys2>:<value2>')
    :param headers: a string containing the header keys divided by space
    :param value: a string value to be split at space
    :return: new_val: the dictionary containing header keys and their values
    """

    # define a dictionary or string to save the new value to
    # (depending on mode)
    new_val = {} if mode == 'dict' else ''
    # iterate over the keys in the header
    for key_index in range(len(headers.split(' '))):

        # return a dictionary
        if mode == 'dict':

            # save the header and value at index 'key_index' in the dictionary
            # (header and value split at ' ' -> lists that are indexed)
            new_val[headers.split(' ')[key_index]] = \
                value.split(' ')[key_index]

        # return a string
        elif mode == 'str':

            # add the header and value at index 'key_index' to the string
            new_val = f'{new_val}{"|" if key_index > 0 else ""}' \
                      f'{headers.split(" ")[key_index]}:"' \
                      f'{value.split(" ")[key_index]}"'

    return new_val


def parse_whitelist_keys(whitelist_keys, value, headers, mode='dict'):
    """
    This function removes the group-key from the end of the value of a plain
    grouped whitelist and splits the value into a dictionary depending on a
    given header
    :param mode: a string defining the type the value split according to the
                 headers should be returned as, default is 'dict'
                 -> dict: returns the split value in a dictionary
                 -> str: returns the split value as a string
                         ('<key1>:<value1>|<keys2>:<value2>')
    :param whitelist_keys: a list of keys the whitelist was grouped by
    :param value: the value that should be converted
    :param headers: a string of keys the value should be split into
                    (might be None if no header is specified)
    :return: value: the converted value (dictionary or string depending on
                    weather a header was given)
    """

    # iterate over whitelist keys
    for k in whitelist_keys:

        # remove the '(<whitelist_key>)' from the end of the value
        if value.endswith(f' ({k})'):
            value = value.replace(f' ({k})', '')

            # test if wi object contains headers
            if headers is not None and k in headers:

                # replace the original value with the one split according to
                # the header
                value = parse_headers(headers[k], value, mode=mode)

            # break since the whitelist key was found in the header
            # -> all other whitelist keys cannot be there too
            # -> better performance
            break

    return value
