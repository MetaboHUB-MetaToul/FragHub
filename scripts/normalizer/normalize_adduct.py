import pandas as pd
import scripts.globals_vars
import re
import os


def normalize_adduct(metadata_dict):
    """
    Normalizes the 'PRECURSORTYPE' (adduct) value in the given metadata dictionary.

    The function first checks for specific instrument types (e.g., GC) to skip
    normalization. It then cleans the adduct string using regular expressions and
    maps common variations to their canonical forms based on global dictionaries.

    :param metadata_dict: The dictionary containing spectrum metadata, including
                          'PRECURSORTYPE' and 'INSTRUMENTTYPE'.
    :type metadata_dict: dict
    :return: The modified metadata dictionary with the normalized adduct value.
    :rtype: dict
    """
    instrument_type = metadata_dict["INSTRUMENTTYPE"]
    # Skip normalization for GC-MS related instrument types.
    if re.search(r"\b(GC)\b", instrument_type, flags=re.IGNORECASE):
        return metadata_dict

    adduct = metadata_dict['PRECURSORTYPE']

    # --- 1. Clean the adduct string using global regex patterns ---
    # Remove common irrelevant parts of the adduct string.
    adduct = re.sub(scripts.globals_vars.sub_adduct_pattern, "", adduct)
    # Remove sign symbols at the end of the adduct string.
    adduct = re.sub(scripts.globals_vars.sub_signe_end_adduct_pattern, "", adduct)

    # --- 2. Map cleaned adduct to canonical form using global dictionaries ---
    # Check and update using the positive adduct dictionary.
    if adduct in scripts.globals_vars.adduct_dict_POS:
        metadata_dict['PRECURSORTYPE'] = scripts.globals_vars.adduct_dict_POS[adduct]

    # Check and update using the negative adduct dictionary.
    if adduct in scripts.globals_vars.adduct_dict_NEG:
        metadata_dict['PRECURSORTYPE'] = scripts.globals_vars.adduct_dict_NEG[adduct]

    return metadata_dict