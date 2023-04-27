def split_value_unit(value_unit):
    """
    This function splits a value_unit (e.g. 2weeks) into a value and unit and
    returns them in a dictionary
    :param value_unit: a string containing a number and a unit
    :return: a dictionary containing value and unit
    """

    # split value and unit
    unit = value_unit.lstrip('0123456789')
    value = int(value_unit[:len(value_unit) - len(unit)])

    return {'value': value, 'unit': unit}


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
