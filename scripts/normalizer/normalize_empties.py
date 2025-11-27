import scripts.globals_vars
import numpy as np
import re


def normalize_empties(metadata_dict):
    """
    Standardizes empty or null-like values within the metadata dictionary to an empty string ('').

    This process handles:
    1. String values that match a predefined "empty pattern" (e.g., 'NA', 'NULL').
    2. Floating-point numbers, including numpy types, that are Not a Number (NaN).

    :param metadata_dict: The dictionary containing spectrum metadata.
    :type metadata_dict: dict
    :return: The metadata dictionary with standardized empty values.
    :rtype: dict
    """
    for k, v in metadata_dict.items():
        # Check if the value is a string.
        if isinstance(v, str):
            # If the string matches the global 'empty_pattern' regex, replace it with an empty string.
            if re.fullmatch(scripts.globals_vars.empty_pattern, v):
                metadata_dict[k] = ''

        # Check if the value is a standard float or a numpy float type AND is NaN.
        elif isinstance(v, (float, np.float64)) and np.isnan(v):
            # Replace NaN values with an empty string for consistency.
            metadata_dict[k] = ''

    return metadata_dict