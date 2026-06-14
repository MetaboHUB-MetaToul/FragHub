// src/normalizer/values_normalizer.rs
use std::collections::HashMap;

pub fn normalize_values(
    mut metadata_dict: HashMap<String, String>,
    deletion_reason: &mut Option<String>,
    context: &super::NormalizerContext
) -> Option<HashMap<String, String>> {

    metadata_dict = super::normalize_empties::normalize_empties(metadata_dict);
    metadata_dict = super::repair_mol_descriptors::repair_mol_descriptors(metadata_dict);

    let metadata_opt = super::delete_no_smiles_no_inchi::delete_no_smiles_no_inchi_no_inchikey(metadata_dict, deletion_reason);
    if metadata_opt.is_none() { return None; }
    metadata_dict = metadata_opt.unwrap();

    // 4. Normalize the Ionization method
    metadata_dict = super::normalize_ionization::normalize_ionization(metadata_dict);

    // 5. Determine and normalize instrument/resolution
    metadata_dict = super::normalize_instruments_and_resolution::normalize_instruments_and_resolution(metadata_dict, context);

    // 6. Normalize the precursor type (adduct)
    metadata_dict = super::normalize_adduct::normalize_adduct(metadata_dict, context);

    // 7. Recalculate missing or invalid PRECURSORMZ
    metadata_dict = super::missing_precursormz_re_calculation::missing_precursormz_re_calculation(metadata_dict, context);

    // 8. Standardize the ionization mode
    metadata_dict = super::normalize_ionmode::normalize_ion_mode(metadata_dict);

    // 9. Standardize the predicted/in-silico status
    metadata_dict = super::normalize_predicted::normalize_predicted(metadata_dict);

    // 10. Validate adduct consistency against the ionization mode; deletes if inconsistent.
    let metadata_opt_2 = super::check_for_bad_adduct::check_for_bad_adduct(metadata_dict, deletion_reason, context);
    if metadata_opt_2.is_none() {
        return None;
    }
    metadata_dict = metadata_opt_2.unwrap();

    // 11. Normalize the MS level.
    metadata_dict = super::normalize_ms_level::normalize_ms_level(metadata_dict);

    // 12. Normalize Retention Time units to minutes.
    metadata_dict = super::normalize_retentiontime::normalize_retention_time(metadata_dict);

    Some(metadata_dict)
}