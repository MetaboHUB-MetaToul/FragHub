from scripts.normalizer.normalize_instruments_and_resolution import normalize_instruments_and_resolution
from scripts.normalizer.missing_precursormz_re_calculation import missing_precursormz_re_calculation
from scripts.normalizer.delete_no_smiles_no_inchi import delete_no_smiles_no_inchi_no_inchikey
from scripts.normalizer.normalize_retentiontime import normalize_retention_time
from scripts.normalizer.repair_mol_descriptors import repair_mol_descriptors
from scripts.normalizer.check_for_bad_adduct import check_for_bad_adduct
from scripts.normalizer.normalize_ionization import normalize_ionization
from scripts.normalizer.normalize_predicted import normalize_predicted
from scripts.normalizer.normalize_ms_level import normalize_ms_level
from scripts.normalizer.normalize_empties import normalize_empties
from scripts.normalizer.normalize_ionmode import normalize_ion_mode
from scripts.normalizer.normalize_adduct import normalize_adduct


def normalize_values(metadata_dict):
    """
    Applies a sequence of normalization and validation functions to standardize
    the values within a spectrum's metadata dictionary.

    The sequence is critical, performing cleanup and structural repair first,
    then checking for mandatory identifiers, and finally normalizing and validating
    physico-chemical properties.

    :param metadata_dict: A dictionary containing spectrum metadata.
    :type metadata_dict: dict
    :return: The normalized metadata dictionary, or None if the spectrum is marked for deletion.
    :rtype: dict or None
    """
    # --- Phase 1: Cleanup and Structural Repair ---
    # 1. Standardize various null/empty representations to an empty string.
    metadata_dict = normalize_empties(metadata_dict)

    # 2. Correct misplacement of chemical identifiers (SMILES, InChI, InChIKey).
    metadata_dict = repair_mol_descriptors(metadata_dict)

    # 3. Check for mandatory chemical identifiers; deletes the spectrum if all are missing.
    metadata_dict = delete_no_smiles_no_inchi_no_inchikey(metadata_dict)

    # --- Phase 2: Property Normalization and Recalculation (requires metadata existence) ---
    if metadata_dict:
        # 4. Normalize the Ionization method (e.g., APCI, ESI).
        metadata_dict = normalize_ionization(metadata_dict)

        # 5. Determine and normalize instrument/resolution based on catalogue lookup.
        metadata_dict = normalize_instruments_and_resolution(metadata_dict)

        # 6. Normalize the precursor type (adduct) to its canonical form.
        metadata_dict = normalize_adduct(metadata_dict)

        # 7. Recalculate/repair missing or invalid PRECURSORMZ using molecular mass and adduct.
        metadata_dict = missing_precursormz_re_calculation(metadata_dict)

        # 8. Standardize the ionization mode ("positive" or "negative").
        metadata_dict = normalize_ion_mode(metadata_dict)

        # 9. Standardize the predicted/in-silico status ("true" or "false").
        metadata_dict = normalize_predicted(metadata_dict)

        # 10. Validate adduct consistency against the ionization mode; deletes if inconsistent.
        metadata_dict = check_for_bad_adduct(metadata_dict)

        # --- Phase 3: Final Property Standardization (requires passing Phase 2 deletion check) ---
        if metadata_dict:
            # 11. Normalize the MS level.
            metadata_dict = normalize_ms_level(metadata_dict)

            # 12. Normalize Retention Time units to minutes.
            metadata_dict = normalize_retention_time(metadata_dict)

    return metadata_dict