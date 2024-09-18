import argparse
import importlib.util as ilu
import json
import os
import sys

print("exec path", os.path.abspath(os.path.join(os.path.dirname(__file__))))
# Add the directory containing the 'src' module to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Provide the absolute path to file_reading.py
file_reading_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "file_reading.py")
)
spec = ilu.spec_from_file_location("file_reading", file_reading_path)
file_reading = ilu.module_from_spec(spec)
spec.loader.exec_module(file_reading)


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process input and output file paths.")
    parser.add_argument("--input", required=True, help="Path to the input JSON file")
    parser.add_argument("--output", required=True, help="Path to the output JSON file")
    args = parser.parse_args()
    get_func_params = {}

    with open(args.input, "r") as f:
        get_func_params = json.loads(f.read())

    metafiles, validation_reports = file_reading.iterate_dir_metafiles(
        get_func_params["key_yaml"],
        get_func_params["path_metafiles"],
        return_false=True,
        run_as_sub=False,
    )

    with open(args.output, "w") as f:
        json.dump(
            {
                "metafiles": metafiles,
                "validation_reports": validation_reports,
            },
            f,
        )


if __name__ == "__main__":
    main()
