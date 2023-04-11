import sys

sys.path.append('metadata-organizer')
import src.utils as utils
import src.web_interface.yaml_to_wi_object as yto
import src.web_interface.git_whitelists as git_whitelists
import os


# This script contains all functions for generation of objects for the web
# interface
disabled_fields = []


def get_empty_wi_object():

    git_whitelists.get_whitelists()

    # read in general structure
    key_yaml = utils.read_in_yaml(os.path.join(os.path.dirname(
        os.path.abspath(__file__)), '..', '..', 'keys.yaml'))

    return yto.get_empty_wi_object(key_yaml)
