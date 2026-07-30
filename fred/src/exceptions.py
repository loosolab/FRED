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
