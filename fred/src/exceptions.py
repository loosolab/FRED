class GoBackSignal(Exception):
    pass


class WhitelistSplitError(ValueError):
    def __init__(self, headers, value, delimiter, header_list, value_list):
        self.headers = headers
        self.value = value
        self.delimiter = delimiter
        self.header_list = header_list
        self.value_list = value_list
        super().__init__(
            f"Whitelist entry '{value}' splits into {len(value_list)} "
            f"part(s) {value_list} using delimiter {delimiter!r}, but "
            f"{len(header_list)} header(s) {header_list} were expected "
            f"(headers: '{headers}'). The whitelist file is malformed."
        )


class WhitelistJoinError(KeyError):
    def __init__(self, headers, value_dict, header_list, missing_key):
        self.headers = headers
        self.value_dict = value_dict
        self.header_list = header_list
        self.missing_key = missing_key
        super().__init__(
            f"Value {value_dict} is missing key '{missing_key}', which is "
            f"required by headers {header_list} (headers: '{headers}')."
        )


class MetadataVersionError(ValueError):
    """
    Raised when a metadata file's recorded 'version' key does not match the
    installed FRED major version (or is missing entirely). The recommended
    migration is always derived from the file's own stored version (stored
    major + 1, as 'X.0.0'), never from the installed version -- migrations
    are only ever cut for major bumps (fred/migrations/vX_0_0/), so naming
    the exact installed version (e.g. a patch release) could point at a
    migration that doesn't exist.
    """

    def __init__(self, path, stored_version):
        self.path = path
        self.stored_version = stored_version
        if stored_version:
            next_migration = f"{int(str(stored_version).split('.')[0]) + 1}.0.0"
        else:
            # missing key == written before FRED tracked versions at all,
            # i.e. predates 3.0.0, the first migration that ever shipped
            next_migration = "3.0.0"
        super().__init__(
            f"Metadata file '{path}' was written with FRED version "
            f"{stored_version or 'unknown (predates version tracking)'}. "
            f"Run 'fred migrate {next_migration}' first."
        )
