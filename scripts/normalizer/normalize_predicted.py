import scripts.globals_vars
import re


def in_filename_or_name(filename, name):
    """
    Checks if the combined filename and spectrum name indicate an in-silico prediction,
    while explicitly excluding data from the "MSMS_Public" source.

    :param filename: The source file name.
    :type filename: str
    :param name: The spectrum name.
    :type name: str
    :return: True if the conditions for in-silico prediction are met and the file is not "MSMS_Public", False otherwise.
    :rtype: bool
    """
    # Exclude files containing "MSMS_Public" from being classified via this check.
    if "MSMS_Public" not in filename:
        # Check if the concatenation of filename and name matches the global In_Silico_pattern.
        if re.search(scripts.globals_vars.In_Silico_pattern, filename + " " + name):
            return True
    return False


def normalize_predicted(metadata_dict):
    """
    Standardizes the 'PREDICTED' field to 'true' or 'false' based on multiple metadata fields.

    The spectrum is classified as 'predicted' (in-silico) if any of the following are true:
    1. The 'COMMENT' field matches the global in-silico pattern.
    2. The original 'PREDICTED' field is already set to 'true'.
    3. The `in_filename_or_name` check returns True.

    If the original 'PREDICTED' field is 'false', it is left unchanged by this function.

    :param metadata_dict: A dictionary containing spectrum metadata, including
                          "COMMENT", "PREDICTED", "FILENAME", and "NAME".
    :type metadata_dict: dict
    :return: The updated metadata dictionary with the standardized 'PREDICTED' field.
    :rtype: dict
    """
    comment_field = metadata_dict["COMMENT"]
    predicted = metadata_dict["PREDICTED"]
    filename = metadata_dict["FILENAME"]
    name = metadata_dict["NAME"]

    # Only attempt to classify as 'true' if the field is not already 'false'.
    if predicted == 'false':
        return metadata_dict

    # Check the conditions to classify the spectrum as predicted ('true').
    if (re.search(scripts.globals_vars.In_Silico_pattern, comment_field) or
            predicted == "true" or
            in_filename_or_name(filename, name)):
        metadata_dict["PREDICTED"] = "true"
    else:
        # If the original field was not 'false' but none of the 'true' conditions were met.
        metadata_dict["PREDICTED"] = "false"

    return metadata_dict