import scripts.globals_vars
import re


def normalize_retention_time(metadata_dict):
    """
    Normalizes the retention time (RT) value in the given metadata dictionary
    to minutes, regardless of the original unit (seconds, milliseconds, or minutes).

    The function searches for a time value and an optional unit using a predefined
    regular expression pattern.

    :param metadata_dict: The dictionary containing the metadata information.
                          It should contain the 'RT' key.
    :type metadata_dict: dict
    :return: The updated metadata dictionary with the normalized 'RT' value in minutes (as a string).
    :rtype: dict
    """

    # Retrieve the retention time from metadata dictionary, ensuring it's a string,
    # or default to an empty string if the key is missing.
    try:
        retientiontime = str(metadata_dict["RT"])
    except:
        retientiontime = ""

    # Search for the retention time pattern (value + optional unit).
    match = re.search(scripts.globals_vars.retention_time_pattern, retientiontime)

    # If the pattern is matched, proceed with normalization.
    if match:
        # Group 1 captures the numerical time value.
        time = match.group(1)

        # Group 2 captures the unit (e.g., 's', 'min', 'ms'). Convert to lowercase.
        unit = match.group(2).lower() if match.group(2) else None

        # --- Normalization Logic ---

        # Case 1: No explicit unit is specified (default to minutes).
        if not unit:
            retientiontime = str(float(time))
            metadata_dict["RT"] = retientiontime
            return metadata_dict
        else:
            # Case 2: Unit is minutes (m, min, minute, minutes). No conversion needed.
            if unit in ["m", "min", "minute", "minutes"]:
                retientiontime = str(float(time))
                metadata_dict["RT"] = retientiontime
                return metadata_dict

            # Case 3: Unit is seconds (s, sec, second, seconds). Convert to minutes (divide by 60).
            elif unit in ["s", "sec", "second", "seconds"]:
                retientiontime = str(float(time) / 60)
                metadata_dict["RT"] = retientiontime
                return metadata_dict

            # Case 4: Unit is milliseconds (ms, millisecond, milliseconds). Convert to minutes (divide by 60,000).
            elif unit in ["ms", "millisecond", "milliseconds"]:
                retientiontime = str(float(time) / 60000)
                metadata_dict["RT"] = retientiontime
                return metadata_dict

    # If the regex pattern is not found, return the metadata dictionary without changes.
    return metadata_dict