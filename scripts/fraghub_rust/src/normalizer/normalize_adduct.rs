// src/normalizer/normalize_adduct.rs
use std::collections::HashMap;

/// Normalise la forme de l'adduct (ex: "[M+H]+" au lieu de "M+H").
///
/// Pour un développeur Python : Remarquez comment le `NormalizerContext` est passé par référence (`&super::NormalizerContext`).
/// Cela permet à cette fonction de consulter les grands dictionnaires d'adducts en RAM sans les copier.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Dictionnaire contenant les métadonnées.
/// * `context` (&super::NormalizerContext) : Contexte global pour vérifier la validité de l'adduct.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec l'adduct standardisé.
pub fn normalize_adduct(mut metadata_dict: HashMap<String, String>, context: &super::NormalizerContext) -> HashMap<String, String> {
    if let Some(inst_type) = metadata_dict.get("INSTRUMENTTYPE") {
        if crate::globals_vars::GC_PATTERN.is_match(inst_type) {
            return metadata_dict; // On ignore les GC
        }
    }

    // `.cloned()` permet d'extraire une copie de la valeur pour la modifier librement.
    if let Some(adduct) = metadata_dict.get("PRECURSORTYPE").cloned() {
        // `.replace_all` renvoie un `Cow` (Copy on Write), `.into_owned()` en fait une `String` mutable.
        let mut cleaned = crate::globals_vars::SUB_ADDUCT_PATTERN.replace_all(&adduct, "").into_owned();

        // Remplacement de sub_signe_end_adduct_pattern: r"(?<!M)(\-|\+)$"
        if (cleaned.ends_with('+') || cleaned.ends_with('-')) && !cleaned.ends_with("M+") && !cleaned.ends_with("M-") {
            cleaned.pop(); // Retire très efficacement le dernier caractère de la chaîne.
        }

        // On consulte le contexte (dictionnaires python transférés en RAM Rust)
        if let Some(canonical) = context.adduct_pos.get(&cleaned) {
            metadata_dict.insert("PRECURSORTYPE".to_string(), canonical.clone());
        } else if let Some(canonical) = context.adduct_neg.get(&cleaned) {
            metadata_dict.insert("PRECURSORTYPE".to_string(), canonical.clone());
        } else {
            metadata_dict.insert("PRECURSORTYPE".to_string(), cleaned);
        }
    }

    metadata_dict
}