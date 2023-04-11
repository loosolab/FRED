import src.wi_utils as wi_utils
import multiprocessing
import copy


def validate_object(wi_object):
    """
    This function performs a validation over the wi object.
    :param wi_object: the filled wi object
    :return: validation_object: the validated wi object with errors and
                                warnings
    """
    pooled = None
    organisms = []
    for setting in wi_object['experimental_setting']['list_value']:
        for elem in setting:
            if elem['position'].split(':')[-1] == 'organism':
                organisms.append(elem['value'].split(' ')[0])
    warnings = {}
    errors = {}
    factors = copy.deepcopy(wi_object['all_factors'])
    wi_object.pop('all_factors')
    arguments = [(elem, wi_object[elem], [], pooled, organisms, []) for elem in
                 wi_object]
    pool_obj = multiprocessing.Pool()
    answer = pool_obj.starmap(wi_utils.validate_part, arguments)

    for elem in answer:
        wi_object[elem[0]] = elem[1]
        warnings[elem[0]] = elem[4]
        errors[elem[0]] = elem[5]

    new_object = {}
    for part in ['project', 'experimental_setting', 'technical_details']:
        new_object[part] = wi_object[part]
    wi_object = new_object
    wi_object['all_factors'] = copy.deepcopy(factors)
    validation_object = {'object': wi_object, 'errors': errors,
                         'warnings': warnings}
    return validation_object
