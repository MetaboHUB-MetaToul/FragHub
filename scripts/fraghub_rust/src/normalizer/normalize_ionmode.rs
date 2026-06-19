// src/normalizer/normalize_ionmode.rs
use std::collections::HashMap;

/// Standardise le champ IONMODE en "positive" ou "negative".
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec IONMODE standardisé.
pub fn normalize_ion_mode(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    if let Some(ion_mode) = metadata_dict.get("IONMODE") {
        if crate::globals_vars::IONMODE_POS_PATTERN.is_match(ion_mode) {
            metadata_dict.insert("IONMODE".to_string(), "positive".to_string());
        } else if crate::globals_vars::IONMODE_NEG_PATTERN.is_match(ion_mode) {
            metadata_dict.insert("IONMODE".to_string(), "negative".to_string());
        }
    }
    metadata_dict
}