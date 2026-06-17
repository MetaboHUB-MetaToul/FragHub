import scripts.globals_vars
import re


def normalize_ionization(metadata_dict):
    """
    Normalizes the ionization mode field in the provided metadata dictionary.

    The function first attempts to extract the ionization mode from the
    'IONIZATION' field. If unsuccessful, it attempts to extract it from the
    'INSTRUMENTTYPE' field. The extracted value is then standardized
    (e.g., correcting 'ACPI' to 'APCI').

    :param metadata_dict: A dictionary containing spectrum metadata, which
                          must include 'IONIZATION' and 'INSTRUMENTTYPE' keys.
    :type metadata_dict: dict
    :return: The modified metadata dictionary with the normalized 'IONIZATION' mode.
    :rtype: dict
    """
    # Attempt to extract ionization mode using a predefined pattern from the 'IONIZATION' field.
    ionization_mode = re.search(scripts.globals_vars.ionization_mode_pattern,
                                metadata_dict["IONIZATION"])

    if ionization_mode:
        # If a match is found, extract the captured group (the mode name).
        ionization_mode = ionization_mode.group(1)

        # Correct known typo: 'ACPI' should be 'APCI'.
        if ionization_mode == "ACPI":
            ionization_mode = "APCI"

        # Update the metadata dictionary with the normalized mode.
        metadata_dict["IONIZATION"] = ionization_mode

    else:
        # If no ionization mode is found in 'IONIZATION', check 'INSTRUMENTTYPE'.
        ionization_mode_in_INSTRUMENTTYPE = re.search(scripts.globals_vars.ionization_mode_pattern,
                                                       metadata_dict["INSTRUMENTTYPE"])

        if ionization_mode_in_INSTRUMENTTYPE:
            # If a match is found in 'INSTRUMENTTYPE', extract the mode name.
            ionization_mode_in_INSTRUMENTTYPE = ionization_mode_in_INSTRUMENTTYPE.group(1)

            # Correct known typo: 'ACPI' should be 'APCI'.
            if ionization_mode_in_INSTRUMENTTYPE == "ACPI":
                ionization_mode_in_INSTRUMENTTYPE = "APCI"

            # Assign the found mode to the 'IONIZATION' field.
            metadata_dict["IONIZATION"] = ionization_mode_in_INSTRUMENTTYPE

    # Final check: if 'IONIZATION' is still None (meaning no mode was found in either field),
    # set it to an empty string for consistency.
    if metadata_dict["IONIZATION"] == None:
        metadata_dict["IONIZATION"] = ''

    # Return the modified dictionary.
    return metadata_dict