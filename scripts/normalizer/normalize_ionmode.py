import scripts.globals_vars
import re


def normalize_ion_mode(metadata_dict):
    """
    Standardizes the ionization mode field ('IONMODE') in the metadata dictionary.

    The function uses predefined regular expression patterns to identify if the
    current value corresponds to a positive or negative ionization mode, and then
    normalizes it to "positive" or "negative" respectively.

    :param metadata_dict: A dictionary containing spectrum metadata, including the "IONMODE" key.
    :type metadata_dict: dict
    :return: The updated metadata dictionary with the "IONMODE" value normalized.
    :rtype: dict
    """

    ion_mode = metadata_dict["IONMODE"]

    # Check if the value matches the pattern for positive ion mode.
    if re.search(scripts.globals_vars.ionmode_pos_pattern, ion_mode):
        ion_mode = "positive"
    # Check if the value matches the pattern for negative ion mode.
    elif re.search(scripts.globals_vars.ionmode_neg_pattern, ion_mode):
        ion_mode = "negative"

    # Update the dictionary with the normalized value.
    metadata_dict["IONMODE"] = ion_mode

    return metadata_dict