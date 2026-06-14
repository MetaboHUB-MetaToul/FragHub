// src/normalizer/normalize_adduct.rs
use std::collections::HashMap;

pub fn normalize_adduct(mut metadata_dict: HashMap<String, String>, context: &super::NormalizerContext) -> HashMap<String, String> {
    if let Some(inst_type) = metadata_dict.get("INSTRUMENTTYPE") {
        if crate::globals_vars::GC_PATTERN.is_match(inst_type) {
            return metadata_dict; // On ignore les GC
        }
    }

    if let Some(adduct) = metadata_dict.get("PRECURSORTYPE").cloned() {
        let mut cleaned = crate::globals_vars::SUB_ADDUCT_PATTERN.replace_all(&adduct, "").into_owned();

        // Remplacement de sub_signe_end_adduct_pattern: r"(?<!M)(\-|\+)$"
        if (cleaned.ends_with('+') || cleaned.ends_with('-')) && !cleaned.ends_with("M+") && !cleaned.ends_with("M-") {
            cleaned.pop();
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