import argparse
import importlib.util as ilu
import json
import os

print("my exec path", os.path.abspath(os.path.join(os.path.dirname(__file__))))

# Set up argument parser
parser = argparse.ArgumentParser(description="Process input and output file paths.")
parser.add_argument("--input", required=True, help="Path to the input JSON file")
parser.add_argument("--output", required=True, help="Path to the output JSON file")
args = parser.parse_args()
get_func_params = {}
