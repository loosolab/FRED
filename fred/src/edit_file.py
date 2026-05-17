from fred.src.generate import Generate
import fred.src.utils as utils
from fred.src.autogenerate import Autogenerate
import os


class Edit(Generate):

    def create_result_dict(self):
        self.result_dict = utils.read_in_yaml(self.path)
        self.id = self.result_dict['project']['id']
    
    def edit(self):
        options = [key for key in self.key_yaml]
        print(
        f"Choose the parts you want to edit (1,...,{len(options)}) divided "
        f"by comma.\n"
        )
        self.print_option_list(options, False)
        edit_keys = self.parse_input_list(options, True)

        for key in edit_keys:

            if key in self.result_dict:
                self.edit_item(self.result_dict[key], [key], 1)
            else:
                self.parse_lists(self.key_yaml[key], [key], 1, self.result_dict)
        
        for elem in self.generate_end:
            func = getattr(Autogenerate, f"get_{elem[-1]}")
            fill_val = func(Autogenerate(self, elem))
            if fill_val is not None:
                self.fill_key(elem, fill_val, self.result_dict)

        utils.save_as_yaml(self.result_dict, self.path)
