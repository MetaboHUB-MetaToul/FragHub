// src/normalizer/normalize_empties.rs
use std::collections::HashMap;

/// Standardise les valeurs vides ou "nulles" du dictionnaire en chaînes vides ("").
/// Équivalent natif et typé de `normalize_empties.py`.
pub fn normalize_empties(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {

    // On itère directement sur des références mutables des valeurs du dictionnaire
    for v in metadata_dict.values_mut() {
        if crate::globals_vars::EMPTY_PATTERN.is_match(v) {
            *v = String::new(); // On remplace par ""
        }
        // NB: Pas besoin de vérifier f64::NAN ici !
        // En Rust, tout est déjà String et le Regex attrape déjà "nan".
    }

    metadata_dict
}