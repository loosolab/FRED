import yaml

# from Mampok

#--------------------------------------------------------------------------------------------------------#
def save_as_yaml(dictionary, file_path):
	''' save dictionary as YAML file
	'''
	with open(file_path, 'w') as file:		# format richtig so?
			documents = yaml.dump(dictionary, file)

#--------------------------------------------------------------------------------------------------------#
def read_in_yaml(yaml_file):
	''' read yaml, auto lower all keys
	Returns: dictionary
	'''
	with open(yaml_file) as file:
		output = yaml.load(file, Loader=yaml.FullLoader)
	low_output = {k.lower(): v for k, v in output.items()}
	return low_output

#--------------------------------------------------------------------------------------------------------#

