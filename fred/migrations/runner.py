import argparse
import importlib
import os


def _version_to_module_name(version):
    return "v" + version.strip().replace(".", "_")


def available_versions():
    migrations_dir = os.path.dirname(__file__)
    return sorted(
        name[1:].replace("_", ".")
        for name in os.listdir(migrations_dir)
        if name.startswith("v")
        and os.path.isdir(os.path.join(migrations_dir, name))
        and os.path.isfile(os.path.join(migrations_dir, name, "migrate.py"))
    )


def run(version, remaining_argv):
    """
    Look up the migration registered for `version`, build an argument parser
    from its add_arguments(), parse `remaining_argv` against it and execute
    the migration.
    """
    module_name = _version_to_module_name(version)
    migrations_dir = os.path.dirname(__file__)
    module_path = os.path.join(migrations_dir, module_name, "migrate.py")

    if not os.path.isfile(module_path):
        versions = available_versions()
        print(f"No migration found for version '{version}'.")
        if versions:
            print(f"Available migration versions: {', '.join(versions)}")
        else:
            print("No migrations are currently available.")
        raise SystemExit(1)

    module = importlib.import_module(f"fred.migrations.{module_name}.migrate")
    migration = module.MIGRATION

    parser = argparse.ArgumentParser(
        prog=f"fred migrate {version}",
        description=f"Run the FRED metadata migration for version {version}",
    )
    migration.add_arguments(parser)
    args = parser.parse_args(remaining_argv)
    migration.run(args)
