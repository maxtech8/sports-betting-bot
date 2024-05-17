import re

from Configurations.StringConstants import SELECT_ADDRESS_REGEX


def is_external_address_request(text_to_check):
    pattern = SELECT_ADDRESS_REGEX
    match = re.match(pattern, text_to_check)
    if match:
        return True
    else:
        return False


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False
