import scripts.deletion_report
import scripts.globals_vars
import re


def check_for_bad_adduct(metadata_dict):
    """
    Validates the consistency of the precursor type (adduct) based on the ionization mode.

    The function applies default adducts if 'PREDICTED' is true and 'PRECURSORTYPE' is empty,
    handles special cases for 'M' adducts, and verifies that the adduct corresponds to
    the correct ionization mode (positive or negative). Invalid or inconsistent spectra
    are recorded for deletion.

    :param metadata_dict: A dictionary containing 'IONMODE', 'PRECURSORTYPE', 'PREDICTED',
                          and 'INSTRUMENTTYPE'.
    :type metadata_dict: dict
    :return: The original metadata dictionary if valid, or None if the spectrum should be deleted.
    :rtype: dict or None
    """
    adduct = metadata_dict['PRECURSORTYPE']
    ion_mode = metadata_dict['IONMODE']
    predicted = metadata_dict['PREDICTED']

    # --- 1. Handle missing adduct if predicted is true ---
    if predicted == "true":
        if not adduct:
            if ion_mode == 'positive':
                # Set default positive adduct.
                metadata_dict['PRECURSORTYPE'] = "[M+H]+"
                adduct = metadata_dict['PRECURSORTYPE']
            elif ion_mode == 'negative':
                # Set default negative adduct.
                metadata_dict['PRECURSORTYPE'] = "[M-H]-"
                adduct = metadata_dict['PRECURSORTYPE']

    # --- 2. Handle specific instrument type (e.g., GC-MS) ---
    instrument_type = metadata_dict["INSTRUMENTTYPE"]
    if re.search(r"\bGC\b", instrument_type):
        if not adduct:
            # Allow empty adduct for GC-MS type instruments without further checks.
            return metadata_dict

    # --- 3. Handle 'M' adduct short form ---
    if adduct == "M":
        if ion_mode == 'positive':
            adduct = "[M]+"
            metadata_dict['PRECURSORTYPE'] = adduct
            return metadata_dict
        elif ion_mode == 'negative':
            adduct = "[M]-"
            metadata_dict['PRECURSORTYPE'] = adduct
            return metadata_dict

    # --- 4. Validate adduct format ---
    if not re.search(scripts.globals_vars.is_adduct_pattern, adduct):
        # Spectrum deleted due to invalid or empty adduct format.
        metadata_dict['DELETION_REASON'] = "spectrum deleted because its adduct field is empty or the value entered is not an adduct"
        scripts.deletion_report.deleted_spectrum_list.append(metadata_dict)
        scripts.deletion_report.no_or_bad_adduct += 1
        return None

    # --- 5. Validate adduct consistency with ionization mode ---
    if ion_mode == 'positive':
        # Check if a positive ion mode spectrum contains a known negative adduct.
        if adduct in scripts.globals_vars.adduct_massdiff_dict_NEG:
            metadata_dict['DELETION_REASON'] = "spectrum deleted because the adduct corresponds to the wrong ionization mode (neg adduct in pos ionmode)."
            scripts.deletion_report.deleted_spectrum_list.append(metadata_dict)
            scripts.deletion_report.no_or_bad_adduct += 1
            return None
        else:
            return metadata_dict

    elif ion_mode == 'negative':
        # Check if a negative ion mode spectrum contains a known positive adduct.
        if adduct in scripts.globals_vars.adduct_massdiff_dict_POS:
            metadata_dict['DELETION_REASON'] = "spectrum deleted because the adduct corresponds to the wrong ionization mode (pos adduct in neg ionmode)."
            scripts.deletion_report.deleted_spectrum_list.append(metadata_dict)
            scripts.deletion_report.no_or_bad_adduct += 1
            return None
        else:
            return metadata_dict

    # Return the dictionary if all checks are passed (especially needed if IONMODE is neither 'positive' nor 'negative').
    return metadata_dict