import src.utils as utils
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.factors_and_conditions as fac_cond
import src.web_interface.wi_utils as wi_utils
import copy

disabled_fields = []

# TODO: code refactoring + documentation


def edit_wi_object(path, key_yaml, read_in_whitelists):
    """
    This function fills an empty wi object with the information of a metadata
    file
    :param key_yaml:
    :param path: the path containing the metadata file
    :return: wi_object: the filled wi object
    """
    # TODO: as Parameter at get_info
    meta_yaml = utils.read_in_yaml(path)
    whitelist_object = {}

    if meta_yaml is not None:
        if "path" in meta_yaml:
            meta_yaml.pop("path")
        empty_object = yto.get_empty_wi_object(key_yaml, read_in_whitelists)
        wi_object = {}
        wi_object["all_factors"], real_val = get_all_factors(meta_yaml, key_yaml)
        wi_object["publication_records"] = get_publication_records(meta_yaml)
        for part in empty_object:
            if part not in ["all_factors", "publication_records"]:
                wi_object[part], whitelist_object = new_fill(
                    meta_yaml[part],
                    empty_object[part],
                    key_yaml[part],
                    whitelist_object,
                    real_val,
                    read_in_whitelists,
                )

    else:
        wi_object = yto.get_empty_wi_object(key_yaml, read_in_whitelists)

    wi_object["whitelists"] = whitelist_object
    wi_object = get_filenames(wi_object, meta_yaml)
    return wi_object


def get_publication_records(meta_yaml):
    publications = list(utils.find_keys(meta_yaml, "publication"))
    publication_records = {}
    for elem in publications:
        for pub in elem:
            if pub["pubmed_id"] not in publication_records:
                publication_records[pub["pubmed_id"]] = pub
    return publication_records


def get_filenames(wi_object, meta_yaml):
    old_filenames = {}
    old_sample_names = {}
    settings = list(utils.find_keys(meta_yaml, "experimental_setting"))
    if len(settings) > 0:
        for setting in settings:
            for stg in setting:
                if "setting_id" in stg:
                    setting_id = stg["setting_id"]
                    bio_reps = list(utils.find_keys(stg, "samples"))
                    if len(bio_reps) > 0:
                        for elem in bio_reps:
                            for sample in elem:
                                if "sample_name" in sample:
                                    key = f'{setting_id}_{sample["sample_name"]}'
                                    tech_rep = list(
                                        utils.find_keys(sample, "technical_replicates")
                                    )
                                    if len(tech_rep) > 0:
                                        if "filenames" in tech_rep[0]:
                                            old_filenames[key] = tech_rep[0][
                                                "filenames"
                                            ]
                                        if "sample_name" in tech_rep[0]:
                                            old_sample_names[key] = tech_rep[0][
                                                "sample_name"
                                            ]
    wi_object["old_sample_names"] = old_sample_names
    wi_object["old_filenames"] = old_filenames
    return wi_object


def new_fill(
    meta_yaml, wi_object, key_yaml, whitelist_object, real_val, read_in_whitelists
):

    if isinstance(meta_yaml, dict):

        if "headers" in wi_object:
            fill_key = "value"
            filled_value = ""
            for header in wi_object["headers"].split(" "):
                filled_value = filled_value + " " + meta_yaml[header]
            filled_value = filled_value.lstrip(" ").rstrip(" ")
        else:
            if wi_object["position"].split(":")[-1] == "experimental_setting":
                fill_key = "input_fields"
                filled_value, whitelist_object = fill_experimental_setting(
                    wi_object,
                    meta_yaml,
                    key_yaml["value"],
                    whitelist_object,
                    real_val,
                    read_in_whitelists,
                )
            else:
                fill_key = "input_fields"
                filled_value = copy.deepcopy(wi_object["input_fields"])
                for i in range(len(filled_value)):
                    if filled_value[i]["position"].split(":")[-1] in meta_yaml:
                        filled_value[i], whitelist_object = new_fill(
                            meta_yaml[filled_value[i]["position"].split(":")[-1]],
                            filled_value[i],
                            key_yaml["value"][
                                filled_value[i]["position"].split(":")[-1]
                            ],
                            whitelist_object,
                            real_val,
                            read_in_whitelists,
                        )

    elif isinstance(meta_yaml, list):
        fill_key = "list_value"
        filled_value = []
        for i in range(len(meta_yaml)):
            f_val, whitelist_object = new_fill(
                meta_yaml[i],
                copy.deepcopy(wi_object),
                key_yaml,
                whitelist_object,
                real_val,
                read_in_whitelists,
            )

            # TODO: WTF?
            if "input_fields" in f_val:
                f_val = f_val["input_fields"]
                if (
                    "position" in f_val
                    and f_val["position"].split(":")[-1] == "experimental_setting"
                ):
                    f_val["input_disabled"] = True
            else:
                f_val = f_val["value"]
            filled_value.append(f_val)

    else:
        fill_key = "value"
        if wi_object["input_type"] == "date":
            filled_value = wi_utils.str_to_date(meta_yaml)
        else:
            filled_value = meta_yaml

    if "input_type" in wi_object and wi_object["input_type"] == "single_autofill":
        fill_key = "list_value"

    wi_object[fill_key] = filled_value

    if "special_case" in key_yaml and "edit" in key_yaml["special_case"]:
        if key_yaml["special_case"]["edit"] == "not editable":
            wi_object["input_disabled"] = True
            wi_object["delete_disabled"] = True
        elif key_yaml["special_case"]["edit"] == "not removable":
            wi_object["delete_disabled"] = True
            if key_yaml["list"]:
                wi_object["fixed_length"] = (
                    len(filled_value) if filled_value is not None else None
                )
                if "input_type" in wi_object and wi_object["input_type"] in [
                    "select",
                    "group_select",
                ]:
                    wi_object["non_editable_val"] = filled_value
    return wi_object, whitelist_object


def fill_experimental_setting(
    wi_object, meta_yaml, key_yaml, whitelist_object, real_val, read_in_whitelists
):
    organism = ""
    filled_object = []
    for j in range(len(wi_object["input_fields"])):
        f = copy.deepcopy(wi_object["input_fields"][j])
        for key in meta_yaml:

            if wi_object["input_fields"][j]["position"].split(":")[-1] == key:
                if key == "experimental_factors":
                    pass
                elif key == "conditions":
                    sample_keys = list(utils.find_keys(key_yaml, "samples"))
                    if len(sample_keys) > 0:

                        sample, whitelists = yto.parse_empty(
                            sample_keys[0],
                            "experimental_setting:conditions:biological_"
                            "replicates:samples",
                            key_yaml,
                            {"organism": organism},
                            read_in_whitelists,
                            get_whitelist_object=True,
                        )
                        sample = sample["input_fields"]

                        conditions = []

                        for cond in meta_yaml[key]:
                            samples = []
                            split_cond = utils.split_cond(cond["condition_name"])
                            sample_name = utils.get_short_name(
                                cond["condition_name"],
                                {},
                                key_yaml,
                                read_in_whitelists=read_in_whitelists,
                            )
                            input_fields = fac_cond.get_samples(
                                split_cond,
                                copy.deepcopy(sample),
                                real_val,
                                key_yaml,
                                sample_name,
                                organism,
                                read_in_whitelists,
                            )
                            if "samples" in cond["biological_replicates"]:
                                for s in cond["biological_replicates"]["samples"]:
                                    filled_keys = []
                                    for k in s:
                                        if s[k] is not None:
                                            # TODO: dict (disease usw.)
                                            # TODO: real_val
                                            if isinstance(s[k], list):
                                                for elem in s[k]:
                                                    if (
                                                        k,
                                                        elem,
                                                    ) not in filled_keys and (
                                                        k,
                                                        elem,
                                                    ) not in split_cond:
                                                        filled_keys.append((k, elem))
                                            elif (k, s[k]) not in split_cond:
                                                filled_keys.append((k, s[k]))
                                    sample_index = int(
                                        s["sample_name"].split("_")[-1].replace("b", "")
                                    )
                                    cond_sample_name = (
                                        f"{sample_name}_" f"{sample_index}"
                                    )
                                    filled_sample = copy.deepcopy(input_fields)
                                    filled_sample = fac_cond.get_samples(
                                        filled_keys,
                                        filled_sample,
                                        real_val,
                                        key_yaml,
                                        cond_sample_name,
                                        organism,
                                        read_in_whitelists,
                                        is_factor=False,
                                    )
                                    samples.append(copy.deepcopy(filled_sample))
                            title, readd = fac_cond.get_condition_title(split_cond)
                            d = {
                                "correct_value": cond["condition_name"],
                                "title": title,
                                "readd": readd,
                                "input_disabled": False,
                                "position": "experimental_setting:condition",
                                "list": True,
                                "mandatory": True,
                                "list_value": samples,
                                "desc": "",
                                "input_fields": input_fields,
                            }
                            if (
                                "special_case" in sample_keys[0]
                                and "edit" in sample_keys[0]["special_case"]
                            ):
                                if (
                                    sample_keys[0]["special_case"]["edit"]
                                    == "not editable"
                                ):
                                    d["input_disabled"] = True
                                    d["delete_disabled"] = True
                                elif (
                                    sample_keys[0]["special_case"]["edit"]
                                    == "not removable"
                                ):
                                    d["delete_disabled"] = True
                                    if sample_keys[0]["list"]:
                                        d["fixed_length"] = (
                                            len(samples)
                                            if samples is not None
                                            else None
                                        )
                            conditions.append(d)
                        # TODO: not editable and not removable for conditions?
                        f["list_value"] = conditions
                        whitelist_object[organism] = whitelists

                else:

                    if "headers" in f and isinstance(meta_yaml[key], dict):
                        new_val = parse_headers(meta_yaml[key], f["headers"])
                    else:
                        new_val = meta_yaml[key]

                    if key == "organism":
                        organism = new_val

                    if "whitelist_keys" in f:
                        new_val = parse_whitelist_keys(
                            meta_yaml[key],
                            f["whitelist_keys"],
                            utils.get_whitelist(
                                key,
                                {"organism": organism},
                                whitelist_object=read_in_whitelists,
                            ),
                        )

                    if "list" in f and f["list"]:
                        f["list_value"] = new_val
                    else:
                        f["value"] = new_val
                filled_object.append(f)
    return filled_object, whitelist_object


def parse_headers(value, headers):

    if isinstance(headers, dict):
        header = None
        for k in headers:
            if sorted(headers[k].split(" ")) == sorted(list(value.keys())):
                header = headers[k].split(" ")
                break
    else:
        header = headers.split(" ")

    if header is not None:
        val = ""
        for h in header:
            val = f'{val}{" " if val != "" else ""}{value[h]}'
        value = val

    return value


def parse_whitelist_keys(value, whitelist_keys, whitelist):

    for key in whitelist_keys:
        if f"{value} ({key})" in whitelist:
            value = f"{value} ({key})"
            break

    return value


# TODO: value unit?
def get_all_factors(meta_yaml, real_val):
    """
    This function creates an object containing all experimental factors from a
    metadata yaml to be stored in a wi object
    :param real_val:
    :param meta_yaml: the read in metadata file
    :return: all_factors: an object containing all experimental factors
    """
    all_factors = []
    for setting in meta_yaml["experimental_setting"]:
        setting_factors = []
        for factors in setting["experimental_factors"]:
            setting_fac = {"factor": factors["factor"]}
            w = utils.get_whitelist(factors["factor"], setting)
            setting_fac["values"] = []
            for elem in factors["values"]:
                value = elem
                if w and "headers" in w:
                    if "headers" not in setting_fac:
                        setting_fac["headers"] = w["headers"]
                    if isinstance(elem, dict):
                        value = parse_headers(value, w["headers"])

                if w and "whitelist_keys" in w:
                    if "whitelist_keys" not in setting_fac:
                        setting_fac["whitelist_keys"] = w["whitelist_keys"]
                    if "whitelist_type" in w and w["whitelist_type"] == "plain_group":
                        value = parse_whitelist_keys(
                            value, w["whitelist_keys"], w["whitelist"]
                        )

                if (
                    isinstance(elem, dict)
                    and len(list(elem.keys())) == 2
                    and "unit" in elem
                    and "value" in elem
                ):
                    value = f'{elem["value"]}{elem["unit"]}'

                if value != elem:
                    if isinstance(elem, dict):
                        # rewrite the value into a string
                        val = "|".join([f'{key}:"{elem[key]}"' for key in elem])
                        val = f'{factors["factor"]}:{"{"}{val}{"}"}'
                        real_val[val] = value
                    else:
                        real_val[elem] = value
                # TODO: nach oben rücken + rekursiv (eigene Funktion)
                elif isinstance(factors["values"], dict):
                    value = {value: factors["values"][value]}
                setting_fac["values"].append(value)
            setting_factors.append(setting_fac)
        all_factors.append(setting_factors)
    return all_factors, real_val
