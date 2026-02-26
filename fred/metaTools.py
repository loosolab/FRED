import argparse
import copy
import pathlib
import sys
import os
import time

sys.path.append(os.path.dirname(__file__))
from fred.src.generate import Generate
from fred.src import find_metafiles
from fred.src import validate_yaml
from fred.src import file_reading
from fred.src import utils
from fred.src import git_whitelists
from fred.src.heatmap import create_heatmap
from fred.src.edit_file import Edit


class FRED:

    def __init__(self, config):
        (
            self.whitelist_repo,
            self.whitelist_branch,
            self.whitelist_path,
            self.username,
            self.password,
            structure,
            self.update_whitelists,
            self.output_path,
            self.filename,
            self.email,
        ) = utils.parse_config(config)
        self.fetch_whitelists()
        self.structure = utils.read_in_yaml(structure)

    def fetch_whitelists(self):
        git_whitelists.get_whitelists(
            self.whitelist_path,
            self.whitelist_repo,
            self.whitelist_branch,
            self.update_whitelists,
        )

    def find(self, search_path, search, output, output_filename, skip_validation):
        result = find_metafiles.find_projects(
            self.structure, search_path, search, True, skip_validation
        )
        if output == "print":
            if len(result) > 0:

                # print summary of matching files
                print(find_metafiles.print_summary(result, output))

            else:

                # print information that there are no matching files
                print("No matches found")
        elif output == "json":
            if not output_filename:
                output_filename = "search_result"
            json_filename = f"{output_filename}.json"
            utils.save_as_json(
                {"data": find_metafiles.print_summary(result, output)}, json_filename
            )
            print(f"The report was saved to the file '{json_filename}'.")

    def generate(self, path, project_id, mandatory_only):
        gen = Generate(
            path, project_id, mandatory_only, self.filename, self.structure, self.email, self.whitelist_path
        )
        gen.generate()

    def validate(
        self, logical_validation, path, output, output_filename, save_empty=False
    ):
        validation_reports = {
            "all_files": 1,
            "corrupt_files": {"count": 0, "report": []},
            "error_count": 0,
            "warning_count": 0,
        }
        if os.path.isdir(path):
            metafiles, validation_reports = file_reading.iterate_dir_metafiles(
                self.structure,
                [path],
                filename=self.filename,
                logical_validation=logical_validation,
                yaml=copy.deepcopy(self.structure),
                whitelist_path=self.whitelist_path,
            )
        else:
            metafile = utils.read_in_yaml(path)
            file_reports = {"file": metafile, "error": None, "warning": None}
            (
                valid,
                missing_mandatory_keys,
                invalid_keys,
                invalid_entries,
                invalid_values,
                logical_warn,
            ) = validate_yaml.validate_file(
                metafile,
                self.structure,
                self.filename,
                logical_validation=logical_validation,
                yaml=copy.deepcopy(self.structure),
                whitelist_path=self.whitelist_path,
            )
            metafile["path"] = str(path)
            if not valid:
                validation_reports["corrupt_files"]["count"] = 1
                validation_reports["error_count"] += (
                    len(missing_mandatory_keys)
                    + len(invalid_keys)
                    + len(invalid_entries)
                    + len(invalid_values)
                )
                file_reports["error"] = (
                    missing_mandatory_keys,
                    invalid_keys,
                    invalid_entries,
                    invalid_values,
                )
            if len(logical_warn) > 0:
                validation_reports["corrupt_files"]["count"] = 1
                validation_reports["warning_count"] += len(logical_warn)
                file_reports["warning"] = logical_warn
            validation_reports["corrupt_files"]["report"].append(file_reports)

        print(f'{validation_reports["all_files"]} files were validated.')
        print(
            f'Found {validation_reports["error_count"]} errors and {validation_reports["warning_count"]} warnings in {validation_reports["corrupt_files"]["count"]} of those files.'
        )

        if validation_reports["corrupt_files"]["count"] > 0 or save_empty is True:

            res = None
            if output is not None:
                if output == "print":
                    res = ["print report"]
                elif output == "txt":
                    res = ["save report to txt file"]
                elif output == "json":
                    res = ["save report to json file"]
                elif output == "yaml":
                    res = ["save report to yaml file"]
            else:
                options = [
                    "print report",
                    "save report to txt file",
                    "save report to json file",
                    "save report to yaml file",
                ]
                print(
                    f"Do you want to see a report? Choose from the following options (1,...,{len(options)} or n)"
                )
                ask = Generate("", "", False, self.filename, self.structure, self.email, self.whitelist_path)
                ask.print_option_list(options, "")
                res = ask.parse_input_list(options, True)

            try:
                output_report = {
                    "report": copy.deepcopy(validation_reports)["corrupt_files"][
                        "report"
                    ]
                }
            except KeyError:
                output_report = {"report": []}
            for elem in output_report["report"]:
                id = list(utils.find_keys(elem["file"], "id"))
                if len(id) > 0:
                    elem["id"] = id[0]
                else:
                    elem["id"] = "missing"
                elem["path"] = elem["file"]["path"]
                errors = (
                    list(elem["error"])
                    if "error" in elem and elem["error"] is not None
                    else []
                )
                elem["error"] = {}
                elem.pop("file")
                for i in range(len(errors)):

                    if len(errors[i]) > 0:
                        if i == 0:
                            elem["error"]["missing_mandatory_keys"] = errors[i]
                        elif i == 1:
                            elem["error"]["invalid_keys"] = errors[i]
                        elif i == 2:
                            whitelist_values = []
                            for v in errors[i]:
                                key = ":".join(v.split(":")[:-1])
                                entry = v.split(":")[-1]
                                whitelist_values.append(entry + " in " + key + "\n")
                            elem["error"]["invalid_entries"] = whitelist_values
                        elif i == 3:
                            value = []
                            for v in errors[i]:
                                value.append(f"{v[0]}: {v[1]} -> {v[2]}")
                            elem["error"]["invalid_values"] = value

                if "warning" in elem:
                    if elem["warning"] is not None:
                        for i in range(len(elem["warning"])):
                            elem["warning"][
                                i
                            ] = f'{elem["warning"][i][0]}: {elem["warning"][i][1]}'
                    else:
                        elem.pop("warning")

            if res is not None:
                if output_filename is None:
                    timestamp = time.time()
                    output_filename = (
                        f'validation_report_{str(timestamp).split(".")[0]}'
                    )

                rep = ""
                for report in validation_reports["corrupt_files"]["report"]:
                    rep += f'{"".center(80, "_")}\n\n'
                    rep += validate_yaml.print_full_report(
                        report["file"], report["error"], report["warning"]
                    )
                rep += f'{"".center(80, "_")}\n\n'

                if "save report to txt file" in res:
                    txt_filename = os.path.join(self.output_path, f"{output_filename}.txt")
                    txt_f = open(txt_filename, "w")
                    txt_f.write(rep)
                    print(f"The report was saved to the file '{txt_filename}'.")
                    txt_f.close()

                if "save report to json file" in res:
                    json_filename = os.path.join(self.output_path, f"{output_filename}.json")
                    utils.save_as_json(output_report, json_filename)
                    print(f"The report was saved to the file '{json_filename}'.")

                if "save report to yaml file" in res:
                    yaml_filename = os.path.join(self.output_path, f"{output_filename}.yaml")
                    utils.save_as_yaml(output_report, yaml_filename)
                    print(f"The report was saved to the file '{yaml_filename}'.")

                if "print report" in res:
                    print(rep)

        return validation_reports["error_count"], validation_reports["warning_count"]

    def edit(self, path, mandatory_only):
        
        edit = Edit(
            path, None, mandatory_only, self.filename, self.structure, self.email, self.whitelist_path
        )
        edit.create_result_dict()
        edit.edit()

    def add_value(self, path, position, value, edit_existing):
        files, errors = file_reading.iterate_dir_metafiles(
            self.structure,
            [path],
            self.filename,
            False,
            return_false=True,
            whitelist_path=self.whitelist_path,
        )
        position = position.split(":")
        # TODO: type
        for file in files:
            file = utils.add_value_at_pos(
                self.structure, file, position, value, edit_existing
            )
            save_path = file["path"]
            file.pop("path")
            print(f"edited file {save_path}")
            utils.save_as_yaml(file, save_path)


def find(args):
    """
    calls script find_metafiles to find matching files and print results
    :param args:
        path: a path of a folder that should be searched for metadata files
        search: a string specifying search parameters linked via 'and', 'or'
                and 'not'
    """
    finding = FRED(args.config)
    finding.find(
        args.path, args.search, args.output, args.filename, args.skip_validation
    )


def generate(args):
    """
    calls script generate_metafile to start dialog
    :param args:
    """
    generating = FRED(args.config)
    generating.generate(args.path, args.id, args.mandatory_only)


def validate(args):
    validating = FRED(args.config)
    errors, warnings = validating.validate(
        not args.skip_logic, args.path, args.output, args.filename
    )


def plot(args):
    fred_object = FRED(args.config)
    input_file = utils.read_in_yaml(args.path)
    plots = create_heatmap.get_heatmap(
        input_file,
        fred_object.structure,
        mode=args.mode,
        labels=args.labels,
        background=args.background,
        sample_labels=args.sample_labels,
        condition_labels=args.condition_labels,
        transpose=args.transpose,
        drop_defaults=args.drop_defaults,
    )
    output_filename = args.filename if args.filename is not None else "fig1"
    if len(plots) > 0:
        try:
            plot = plots[args.setting - 1][1]
        except IndexError:
            print(f"Setting exp{args.setting} does not exist. Defaulting to exp1.")
            plot = plots[0][1]

        if plot is not None:
            if args.output == "png":
                plot.write_image(os.path.join(fred_object.output_path, f"{output_filename}.{args.output}"), format="png")
                print(f"Plot was saved to {fred_object.output_path}/{output_filename}.{args.output}")
            elif args.output == "html":
                with open(os.path.join(fred_object.output_path,f"{output_filename}.{args.output}"), "w") as file:
                    file.write(plot.to_html(full_html=False, include_plotlyjs="cdn"))
                print(f"Plot was saved to {fred_object.output_path}/{output_filename}.{args.output}")
            else:
                plot.show()
        else:
            print("Plot could not be created due to missing samples or conditions.")
    else:
        print("No settings found.")


def edit(args):
    editing = FRED(args.config)
    editing.edit(args.path, args.mandatory_only)


def add_value(args):
    adding = FRED(args.config)
    adding.add_value(args.path, args.position, args.value, args.edit_existing)


def main():

    parser = argparse.ArgumentParser(prog="metaTools.py")
    subparsers = parser.add_subparsers(title="commands")

    # Generate Function
    create_function = subparsers.add_parser(
        "generate", 
        help="Generate a metadata file"
    )
    create_group = create_function.add_argument_group("mandatory arguments")
    create_group.add_argument(
        "-p",
        "--path",
        type=pathlib.Path,
        required=True,
        help="Path the generated file is saved to",
    )
    create_group.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        help="Config file",
        default=os.path.join(os.path.dirname(__file__), "config", "config.yaml"),
    )
    create_group.add_argument(
        "-id", 
        "--id", 
        type=str, 
        required=True, 
        help="The ID of the project"
    )
    create_function.add_argument(
        "-mo",
        "--mandatory_only",
        default=False,
        action="store_true",
        help="Set True to only fill mandatory keys",
    )
    create_function.set_defaults(func=generate)

    # Find Function
    find_function = subparsers.add_parser(
        "find",
        help="Find metadata files",
    )

    find_group = find_function.add_argument_group("mandatory arguments")
    find_group.add_argument(
        "-p", 
        "--path", 
        type=pathlib.Path, 
        required=True, 
        help="Path to be searched in"
    )
    find_group.add_argument(
        "-s", 
        "--search", 
        type=str, 
        required=True, 
        help="Search string"
    )
    find_group.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        help="Config file",
        default=os.path.join(os.path.dirname(__file__), "config", "config.yaml"),
    )
    find_group.add_argument(
        "-o", 
        "--output", 
        default="print", 
        choices=["json", "print"],
        help="Save or display output"
    )
    find_group.add_argument(
        "-f", 
        "--filename", 
        default=None,
        help="File output is saved to if it is not printed")
    find_group.add_argument(
        "-sv", 
        "--skip_validation", 
        default=False, 
        action="store_true",
        help="Set to skip validation"
    )
    find_function.set_defaults(func=find)

    # Validation Function
    validate_function = subparsers.add_parser(
        "validate", 
        help="Validate Metadata")
    validate_group = validate_function.add_argument_group("mandatory arguments")
    validate_group.add_argument(
        "-p", 
        "--path", 
        type=pathlib.Path, 
        required=True,
        help="Path to metadata file or folder")
    validate_function.add_argument(
        "-l", 
        "--skip_logic", 
        default=False, 
        action="store_true",
        help="Set to skip logical validation"
    )
    validate_function.add_argument(
        "-o", 
        "--output",
        default=None,
        choices=["json", "txt", "print", "yaml"],
        help="Select how the report should be displayed/saved"
    )
    validate_function.add_argument(
        "-f", 
        "--filename", 
        default=None,
        help="Filename of the report")
    validate_function.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        help="Config file",
        default=os.path.join(os.path.dirname(__file__), "config", "config.yaml"),
    )
    validate_function.set_defaults(func=validate)

    # EDIT Funtion
    edit_function = subparsers.add_parser(
        'edit', 
        help='Edit a metadata file')
    edit_group = edit_function.add_argument_group('mandatory_arguments')
    edit_group.add_argument(
        '-p', 
        '--path', 
        type=pathlib.Path, 
        required=True,
        help="Path of the file to edit")
    edit_function.add_argument(
        '-mo', 
        '--mandatory_only', 
        default=False,
        action='store_true',
        help='Set True to only fill mandatory keys')
    edit_function.add_argument(
        '-c', 
        '--config', 
        type=pathlib.Path,
        help='Config file', 
        default=os.path.join(os.path.dirname(__file__), "config", "config.yaml"))
    edit_function.set_defaults(func=edit)

    # Plot Function
    plot_function = subparsers.add_parser(
        "plot", 
        help="Plot an experiment")
    plot_function.add_argument(
        "-p", 
        "--path", 
        type=pathlib.Path, 
        required=True,
        help="Path to metadata file")
    plot_function.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        help="Config file",
        default=os.path.join(os.path.dirname(__file__), "config", "config.yaml"),
    )
    plot_function.add_argument(
        "-m", 
        "--mode", 
        default="samples", 
        choices=["samples", "conditions"],
        help="Define if samples or conditions are displayed"
    )
    plot_function.add_argument(
        "-s", 
        "--setting", 
        type=int, 
        default=1,
        help="Number of the experimental setting that should be displayed (e.g. 1 for exp1, 2 for exp2, ...)")
    plot_function.add_argument(
        "-l", 
        "--labels", 
        default="factors", 
        choices=["factors", "all", "none"],
        help="Define which cells should have labels"
    )
    plot_function.add_argument(
        "-o", 
        "--output", 
        default="show", 
        choices=["show", "png", "html"],
        help="Define how to display/save the plot"
    )
    plot_function.add_argument(
        "-f", 
        "--filename", 
        type=pathlib.Path,
        help="Filename of the plot")
    plot_function.add_argument(
        "-b",
        "--background",
        default=False,
        action="store_true",
        help="State for the background to be displayed in white. Per default it is transparent.",
    )
    plot_function.add_argument(
        "-cl",
        "--condition_labels",
        default=False,
        action="store_true",
        help="State to display the label of the condition as a name. Per default an index is stated. ",
    )
    plot_function.add_argument(
        "-sl",
        "--sample_labels",
        default=False,
        action="store_true",
        help="State to display the label of the sample as a name. Per default an index is stated. ",
    )
    plot_function.add_argument(
        "-t",
        "--transpose",
        default=False,
        action="store_true",
        help="Transpose the plot"
    )
    plot_function.add_argument(
        "-d",
        "--drop_defaults",
        default=False,
        action="store_true",
        help="Drop all properties, that only contain default values"
    )
    plot_function.set_defaults(func=plot)

    args = parser.parse_args()

    try:
        args.func(args)
    except AttributeError:
        parser.print_help()


if __name__ == "__main__":

    main()
