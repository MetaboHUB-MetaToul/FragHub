import scripts.deletion_report


def delete_no_smiles_no_inchi_no_inchikey(metadata_dict):
    """
    Deletes a spectrum if the metadata lacks all three essential chemical identifiers:
    SMILES, InChI, and InChIKey.

    The function checks if the values for 'SMILES', 'INCHI', and 'INCHIKEY' are
    all non-existent (evaluated as False, typically meaning None or NaN).

    :param metadata_dict: A dictionary containing chemical metadata.
    :type metadata_dict: dict
    :return: The original metadata dictionary if at least one identifier is present,
             or None if all three are missing.
    :rtype: dict or None
    """
    # Check if all three identifiers (SMILES, INCHI, INCHIKEY) evaluate to False (e.g., empty string, None, or NaN).
    if not metadata_dict["SMILES"] and not metadata_dict["INCHI"] and not metadata_dict["INCHIKEY"]:
        # If all identifiers are missing, record the deletion reason and update the report counter.
        metadata_dict['DELETION_REASON'] = "spectrum deleted because it has neither inchi nor smiles nor inchikey"
        scripts.deletion_report.deleted_spectrum_list.append(metadata_dict)
        scripts.deletion_report.no_smiles_no_inchi_no_inchikey += 1
        return None
    else:
        # If at least one identifier is present, the spectrum is kept.
        return metadata_dict