import scripts.globals_vars
import json
import re


def clean_instrument(instrument):
    """
    Cleans the main instrument name string by standardizing vendor/model names
    and abbreviations.

    :param instrument: The raw instrument name string.
    :type instrument: str
    :return: The cleaned instrument name string.
    :rtype: str
    """
    # Standardize 'tof' terminology
    instrument = re.sub("-tof", "tof", instrument)

    # Standardize 'q' terminology
    instrument = re.sub("q-", "q", instrument)

    # Standardize 'q exactive' spacing/casing
    instrument = re.sub("q exactive", " qexactive ", instrument)

    # Standardize Applied Biosystems to Sciex
    instrument = re.sub("applied biosystems", " sciex ", instrument)
    instrument = re.sub(" ab ", " sciex ", instrument)

    # Ensure 'sciex' is always surrounded by spaces for better word boundary matching
    instrument = re.sub("sciex", " sciex ", instrument)

    # Standardize Triple-TOF/Quad to 'qqq' (Triple Quadrupole)
    instrument = re.sub("triple(-| )?tof", " qqq ", instrument)
    instrument = re.sub("triple(-| )?quad", " qqq ", instrument)

    # Remove UPLC annotations
    instrument = re.sub("... uplc ...", " ", instrument)

    return instrument


def clean_instrument_type(instrument_type):
    """
    Cleans the instrument type string by standardizing terms and removing hyphens.

    :param instrument_type: The raw instrument type string.
    :type instrument_type: str
    :return: The cleaned instrument type string.
    :rtype: str
    """
    # Standardize 'tof' terminology
    instrument_type = re.sub("-tof", "tof", instrument_type)

    # Standardize 'q' terminology
    instrument_type = re.sub("q-", "q", instrument_type)

    # Replace all hyphens with spaces for easier word matching
    instrument_type = re.sub("-", " ", instrument_type)

    # Standardize 'q exactive' spacing/casing
    instrument_type = re.sub("q exactive", " qexactive ", instrument_type)

    # Standardize Applied Biosystems to Sciex
    instrument_type = re.sub("applied biosystems", " sciex ", instrument_type)
    instrument_type = re.sub(" ab ", " sciex ", instrument_type)

    # Ensure 'sciex' is always surrounded by spaces for better word boundary matching
    instrument_type = re.sub("sciex", " sciex ", instrument_type)

    # Standardize Triple-TOF/Quad to 'qqq' (Triple Quadrupole)
    instrument_type = re.sub("triple(-| )?tof", " qqq ", instrument_type)
    instrument_type = re.sub("triple(-| )?quad", " qqq ", instrument_type)

    # Remove UPLC annotations
    instrument_type = re.sub("... uplc ...", " ", instrument_type)

    return instrument_type


def clean_comment(comment):
    """
    Cleans the comment string by standardizing terms and replacing hyphens with spaces.

    :param comment: The raw comment string.
    :type comment: str
    :return: The cleaned comment string.
    :rtype: str
    """
    # Standardize 'tof' terminology
    comment = re.sub("-tof", "tof", comment)

    # Standardize 'q' terminology
    comment = re.sub("q-", "q", comment)

    # Replace all hyphens with spaces for easier word matching
    comment = re.sub("-", " ", comment)

    # Standardize 'q exactive' spacing/casing
    comment = re.sub("q exactive", " qexactive ", comment)

    # Standardize Applied Biosystems to Sciex
    comment = re.sub("applied biosystems", " sciex ", comment)
    comment = re.sub(" ab ", " sciex ", comment)

    # Ensure 'sciex' is always surrounded by spaces for better word boundary matching
    comment = re.sub("sciex", " sciex ", comment)

    # Standardize Triple-TOF/Quad to 'qqq' (Triple Quadrupole)
    comment = re.sub("triple(-| )?tof", " qqq ", comment)
    comment = re.sub("triple(-| )?quad", " qqq ", comment)

    # Remove UPLC annotations
    comment = re.sub("... uplc ...", " ", comment)

    return comment


def clean_spectrum_instrument_info(metadata_dict):
    """
    Combines and cleans instrument-related metadata fields into a single,
    standardized string for catalog matching.

    :param metadata_dict: A dictionary containing the spectrum metadata.
    :type metadata_dict: dict
    :return: A single string containing all cleaned instrument information.
    :rtype: str
    """
    # Extract instrument information and convert to lowercase for case-insensitive matching
    instrument = metadata_dict['INSTRUMENT'].lower()
    instrument_type = metadata_dict["INSTRUMENTTYPE"].lower()
    comment = metadata_dict["COMMENT"].lower()

    # Clean individual fields
    instrument = clean_instrument(instrument)
    instrument_type = clean_instrument_type(instrument_type)
    comment = clean_comment(comment)

    # Combine the cleaned information into one string
    instrument_infos = instrument + " " + instrument_type + " " + comment

    # Remove any non-word, non-whitespace, and non-hyphen characters,
    # normalize whitespace, and strip leading/trailing spaces
    instrument_infos = re.sub(r'[^-\w\s]', ' ', instrument_infos)
    instrument_infos = ' '.join(instrument_infos.split()).strip()

    return instrument_infos


def search_for_brand(tree_path, instrument_infos):
    """
    Searches for the instrument brand (first level of the instrument tree)
    within the instrument information string.

    :param tree_path: Current list representing the path in the instrument tree.
    :type tree_path: list
    :param instrument_infos: String containing information about the instrument.
    :type instrument_infos: str
    :return: The updated tree_path list with the found brand or 'not found'. Returns None on exception.
    :rtype: list or None
    """
    try:
        # Iterate over all possible brands (top-level keys of the instrument tree)
        for key in scripts.globals_vars.instrument_tree.keys():
            # Search for the brand key, ensuring it's a whole word boundary match
            if re.search(rf"(\b|^|$){key}(\b|^|$)", instrument_infos):
                tree_path.append(key)
                return tree_path

        # If no brand is found, append 'not found'
        tree_path.append('not found')
        return tree_path

    except:
        return None


def search_for_model(tree_path, instrument_infos):
    """
    Searches for the instrument model (second level) based on the previously found brand.

    :param tree_path: Current path, including the brand (tree_path[0]).
    :type tree_path: list
    :param instrument_infos: String containing instrument information.
    :type instrument_infos: str
    :return: The updated tree_path list with the found model or 'not found'. Returns None on exception.
    :rtype: list or None
    """
    try:
        # Access the models under the previously found brand (tree_path[0])
        for key in scripts.globals_vars.instrument_tree[tree_path[0]].keys():
            # Search for the model key with word boundaries
            if re.search(rf"(\b|^|$){key}(\b|^|$)", instrument_infos):
                tree_path.append(key)
                return tree_path

        # If no model is found, append 'not found'
        tree_path.append('not found')
        return tree_path

    except:
        # Handle exceptions like KeyError if tree_path[0] was 'not found'
        return None


def search_for_spectrum_type(tree_path, instrument_infos):
    """
    Searches for the spectrum type (third level) based on the found brand and model.

    :param tree_path: Current path, including brand and model (tree_path[0], tree_path[1]).
    :type tree_path: list
    :param instrument_infos: String containing instrument information.
    :type instrument_infos: str
    :return: The updated tree_path list with the found spectrum type or 'not found'. Returns None on exception.
    :rtype: list or None
    """
    try:
        # Access the spectrum types under the found brand and model
        for key in scripts.globals_vars.instrument_tree[tree_path[0]][tree_path[1]].keys():
            # Search for the spectrum type key with word boundaries
            if re.search(rf"(\b|^|$){key}(\b|^|$)", instrument_infos):
                tree_path.append(key)
                return tree_path

        # If no spectrum type is found, append 'not found'
        tree_path.append('not found')
        return tree_path

    except:
        # Handle exceptions like KeyError if previous path components were 'not found'
        return None


def search_for_instrument_type(tree_path, instrument_infos):
    """
    Searches for the specific instrument type (fourth level) based on the preceding path.

    :param tree_path: Current path, including brand, model, and spectrum type.
    :type tree_path: list
    :param instrument_infos: String containing instrument information.
    :type instrument_infos: str
    :return: The updated tree_path list with the found instrument type or 'not found'. Returns None on exception.
    :rtype: list or None
    """
    try:
        # Access the instrument types at the fourth level of the instrument tree
        for key in scripts.globals_vars.instrument_tree[tree_path[0]][tree_path[1]][tree_path[2]].keys():
            # Search for the instrument type key with word boundaries
            if re.search(rf"(\b|^|$){key}(\b|^|$)", instrument_infos):
                tree_path.append(key)
                return tree_path

        # If no instrument type is found, append 'not found'
        tree_path.append('not found')
        return tree_path

    except:
        # Handle exceptions if previous path components were 'not found'
        return None


def search_for_ionisation(tree_path, instrument_infos):
    """
    Searches for the ionisation method (fifth level) based on the preceding path.

    :param tree_path: Current path, including brand, model, spectrum type, and instrument type.
    :type tree_path: list
    :param instrument_infos: String containing instrument information.
    :type instrument_infos: str
    :return: The updated tree_path list with the found ionisation method or 'not found'. Returns None on exception.
    :rtype: list or None
    """
    try:
        # Access the ionisation methods at the fifth level of the instrument tree
        for key in scripts.globals_vars.instrument_tree[tree_path[0]][tree_path[1]][tree_path[2]][tree_path[3]].keys():
            # Search for the ionisation method key with word boundaries
            if re.search(rf"(\b|^|$){key}(\b|^|$)", instrument_infos):
                tree_path.append(key)
                return tree_path

        # If no ionisation method is found, append 'not found'
        tree_path.append('not found')
        return tree_path

    except:
        # Handle exceptions if previous path components were 'not found'
        return None


def make_tree_path(instrument_infos):
    """
    Constructs the full, five-level path (Brand, Model, Spectrum Type,
    Instrument Type, Ionisation) in the instrument tree based on the
    cleaned instrument information string.

    The path construction stops and returns None if any step fails to find
    a valid key and throws an exception (which typically means a preceding
    search returned 'not found' and a subsequent function tried to access it).

    :param instrument_infos: The cleaned and combined instrument information string.
    :type instrument_infos: str
    :return: A list representing the path in the instrument tree, or None if
             the path construction fails.
    :rtype: list or None
    """
    tree_path = []

    # 1. Search for Brand
    tree_path = search_for_brand(tree_path, instrument_infos)
    if not tree_path:
        return None

    # 2. Search for Model
    tree_path = search_for_model(tree_path, instrument_infos)
    if not tree_path:
        return None

    # 3. Search for Spectrum Type
    tree_path = search_for_spectrum_type(tree_path, instrument_infos)
    if not tree_path:
        return None

    # 4. Search for Instrument Type
    tree_path = search_for_instrument_type(tree_path, instrument_infos)
    if not tree_path:
        return None

    # 5. Search for Ionisation
    tree_path = search_for_ionisation(tree_path, instrument_infos)
    if not tree_path:
        return None

    return tree_path


def normalize_instruments_and_resolution(metadata_dict):
    """
    Normalizes the instrument and resolution fields in the metadata dictionary
    by matching the raw instrument information against a predefined catalogue
    (instrument_tree).

    If a match is found, the fields 'INSTRUMENT', 'INSTRUMENTTYPE',
    'RESOLUTION', and potentially 'IONIZATION' are updated with the
    standardized values defined in the catalogue.

    :param metadata_dict: A dictionary containing metadata with raw
                          'INSTRUMENT', 'INSTRUMENTTYPE', and 'COMMENT' fields.
    :type metadata_dict: dict
    :return: The modified metadata dictionary with standardized instrument info.
    :rtype: dict
    """
    # 1. Combine and Clean Raw Instrument Info
    instrument_infos = clean_spectrum_instrument_info(metadata_dict)

    # Wrap the information with spaces and periods for better boundary matching in 'make_tree_path'
    instrument_infos = f". {instrument_infos} ."

    # 2. Build Path in Instrument Tree
    tree_path = make_tree_path(instrument_infos)

    # If the path could not be fully determined, return the metadata unaltered
    if not tree_path:
        return metadata_dict

    # 3. Retrieve Standardization Solution (Resolution and Standardized Names)
    try:
        # Check the 6th level of the tree (under the Ionisation key) for resolution information
        resolution_level = scripts.globals_vars.instrument_tree[tree_path[0]][tree_path[1]][tree_path[2]][tree_path[3]][tree_path[4]]

        # Determine if the resolution is 'high', 'low', or 'unknown' based on keys present
        resolution = "high" if "high" in resolution_level else \
                     "low" if "low" in resolution_level else \
                     "unknown"

        # Retrieve the standardized solution string (e.g., "Instrument A, Type B, Resolution C")
        solution = resolution_level[resolution]["SOLUTION"]

        # The solution string is comma-separated: Instrument, InstrumentType, Resolution
        solution = solution.split(',')
    except:
        # If any retrieval error occurs (e.g., KeyError), return the metadata unaltered
        return metadata_dict

    # 4. Update Metadata Fields
    metadata_dict["INSTRUMENT"] = solution[0].strip()
    metadata_dict["INSTRUMENTTYPE"] = solution[1].strip()
    metadata_dict["RESOLUTION"] = solution[2].strip()

    # If the standardized instrument type contains a hyphenated ionisation method, extract it
    if len(solution[1].split('-')) >= 2:
        metadata_dict["IONIZATION"] = solution[1].split('-')[1].strip()

    return metadata_dict