import scripts.globals_vars
import re


def repair_inchi(metadata_dict):
    """
    Fixes the 'INCHI' value by ensuring it starts with the canonical prefix "InChI=".

    This function replaces common incorrect leading patterns in the InChI string
    with the required prefix, if the 'INCHI' field is not empty.

    :param metadata_dict: A dictionary containing spectrum metadata, including the 'INCHI' key.
    :type metadata_dict: dict
    :return: The metadata dictionary with the potentially updated 'INCHI' string.
    :rtype: dict
    """
    inchi = metadata_dict.get('INCHI')

    if inchi:
        # Replace the determined incorrect pattern with the canonical "InChI=".
        inchi = re.sub(scripts.globals_vars.repair_inchi_pattern, "InChI=", inchi)
        metadata_dict['INCHI'] = inchi

    return metadata_dict


def repair_mol_descriptors(metadata_dict):
    """
    Corrects common misplacements of molecular descriptors (SMILES, InChI, InChIKey)
    among their respective fields in the metadata dictionary.

    The function checks if a field contains a value that matches the pattern of
    a *different* descriptor and swaps them accordingly to place the descriptor
    in its correct key (e.g., if SMILES is found in the INCHI field, it is moved
    to the SMILES field).

    :param metadata_dict: A dictionary containing spectrum metadata with keys:
                          'SMILES', 'INCHI', and 'INCHIKEY'.
    :type metadata_dict: dict
    :return: The metadata dictionary with standardized descriptor placement.
    :rtype: dict
    """
    # Use local variables for easier access and modification.
    smiles = metadata_dict['SMILES']
    inchi = metadata_dict['INCHI']
    inchikey = metadata_dict['INCHIKEY']

    # --- Initial Check for Correct Placement ---
    # If all fields are correctly formatted, apply InChI repair and return early.
    if (re.search(scripts.globals_vars.smiles_pattern, smiles) and
            re.search(scripts.globals_vars.inchi_pattern, inchi) and
            re.search(scripts.globals_vars.inchikey_pattern, inchikey)):
        metadata_dict = repair_inchi(metadata_dict)
        return metadata_dict

    # --- Cross-Field Repair Logic ---
    # Note: These checks are sequential. If a value is moved, its original field
    # becomes blank (''), preventing infinite loops or double-swapping based on old values.

    # 1. SMILES found in INCHI field: Move INCHI content to SMILES, clear INCHI.
    if re.search(scripts.globals_vars.smiles_pattern, inchi):
        if not re.search(scripts.globals_vars.inchi_pattern, inchi) and not re.search(scripts.globals_vars.inchikey_pattern, inchi):
            metadata_dict['SMILES'] = inchi
            metadata_dict['INCHI'] = ''

    # 2. SMILES found in INCHIKEY field: Move INCHIKEY content to SMILES, clear INCHIKEY.
    if re.search(scripts.globals_vars.smiles_pattern, inchikey):
        if not re.search(scripts.globals_vars.inchi_pattern, inchikey) and not re.search(scripts.globals_vars.inchikey_pattern, inchikey):
            metadata_dict['SMILES'] = inchikey
            metadata_dict['INCHIKEY'] = ''

    # 3. INCHI pattern found in SMILES field: Move SMILES content to INCHI, clear SMILES.
    if re.search(scripts.globals_vars.inchi_pattern, smiles):
        metadata_dict['INCHI'] = smiles
        metadata_dict['SMILES'] = ''

    # 4. INCHI pattern found in INCHIKEY field: Move INCHIKEY content to INCHI, clear INCHIKEY.
    if re.search(scripts.globals_vars.inchi_pattern, inchikey):
        metadata_dict['INCHI'] = inchikey
        metadata_dict['INCHIKEY'] = ''

    # 5. INCHIKEY pattern found in INCHI field: Move INCHI content to INCHIKEY, clear INCHI.
    if re.search(scripts.globals_vars.inchikey_pattern, inchi):
        metadata_dict['INCHIKEY'] = inchi
        metadata_dict['INCHI'] = ''

    # 6. INCHIKEY pattern found in SMILES field: Move SMILES content to INCHIKEY, clear SMILES.
    if re.search(scripts.globals_vars.inchikey_pattern, smiles):
        metadata_dict['INCHIKEY'] = smiles
        metadata_dict['SMILES'] = ''

    # Final step: Ensure the INCHI field has the correct prefix after any potential swaps.
    metadata_dict = repair_inchi(metadata_dict)

    return metadata_dict