import re

global ionmode_pos_pattern
ionmode_pos_pattern = re.compile(r"^p|^\+|^pos", flags=re.IGNORECASE)

global ionmode_neg_pattern
ionmode_neg_pattern = re.compile(r"^n|^\-|^neg", flags=re.IGNORECASE)

def normalize_ionmode(metadata_dict):
    """
    :param metadata_dict: A dictionary containing metadata information.
        It should have the key "IONMODE" to represent the ionization mode.
    :return: The updated metadata dictionary with the "IONMODE" value normalized to either "positive" or "negative".
    """

    # get the value of "IONMODE" from the metadata dictionary
    ionmode = metadata_dict["IONMODE"]

    # If the pattern for positive ion mode is found in ion mode, change it to normalized form "positive"
    if re.search(ionmode_pos_pattern, ionmode):
        ionmode = "positive"
    # If the pattern for negative ion mode is found in ion mode, change it to normalized form "negative"
    elif re.search(ionmode_neg_pattern, ionmode):
        ionmode = "negative"

    # update the "IONMODE" key in metadata dictionary with normalized ion mode value
    metadata_dict["IONMODE"] = ionmode

    # return the updated metadata dictionary
    return metadata_dict