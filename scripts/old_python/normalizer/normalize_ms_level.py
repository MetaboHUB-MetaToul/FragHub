import scripts.globals_vars
import re


def normalize_ms_level(metadata_dict):
    """
    Normalizes the MS level field ('MSLEVEL') in the metadata dictionary.

    The function attempts to extract numeric MS level(s) using a predefined regex pattern.
    If one level is found, it is used. If multiple levels are found (e.g., in a range),
    the first two are combined as a range (e.g., "3-4"). If the field is missing or
    no pattern is matched, 'MSLEVEL' defaults to "2".

    :param metadata_dict: The dictionary containing spectrum metadata.
    :type metadata_dict: dict
    :return: The updated metadata dictionary with the normalized MS level value.
    :rtype: dict
    """
    ms_level = None

    # Retrieve MS level value, ensuring it's handled as a string.
    try:
        ms_level = str(metadata_dict["MSLEVEL"])
    except KeyError:
        # If "MSLEVEL" key is missing, ms_level remains None.
        pass
    except Exception:
        # Handle other potential exceptions during string conversion.
        pass

    if ms_level:
        # Find all numerical occurrences matching the global MS level pattern.
        matched_levels = re.findall(scripts.globals_vars.ms_level_pattern, ms_level)

        if matched_levels:
            if len(matched_levels) == 1:
                # If a single level is found, use it.
                metadata_dict["MSLEVEL"] = matched_levels[0]

            elif len(matched_levels) >= 2:
                # If a range or multiple levels are found, use the first two to define a range.
                metadata_dict["MSLEVEL"] = f"{matched_levels[0]}-{matched_levels[1]}"

        else:
            # If the key existed but no valid pattern was matched, default to "2".
            metadata_dict["MSLEVEL"] = "2"

    else:
        # If the key was missing or its value was effectively None, default to "2".
        metadata_dict["MSLEVEL"] = "2"

    return metadata_dict