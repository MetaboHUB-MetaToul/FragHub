// src/normalizer/normalize_ionization.rs
use std::collections::HashMap;

/// Normalise le mode d'ionisation en lisant IONIZATION ou INSTRUMENTTYPE
pub fn normalize_ionization(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let mut found_mode: Option<String> = None;

    // 1. Chercher d'abord dans IONIZATION
    if let Some(ion) = metadata_dict.get("IONIZATION") {
        if let Some(caps) = crate::globals_vars::IONIZATION_MODE_PATTERN.captures(ion) {
            if let Some(m) = caps.get(1) {
                // On met en majuscules pour garantir la correction de la faute de frappe
                found_mode = Some(m.as_str().to_uppercase());
            }
        }
    }

    // 2. Si rien n'est trouvé, chercher dans INSTRUMENTTYPE
    if found_mode.is_none() {
        if let Some(inst) = metadata_dict.get("INSTRUMENTTYPE") {
            if let Some(caps) = crate::globals_vars::IONIZATION_MODE_PATTERN.captures(inst) {
                if let Some(m) = caps.get(1) {
                    found_mode = Some(m.as_str().to_uppercase());
                }
            }
        }
    }

    // 3. Application et correction
    if let Some(mut mode) = found_mode {
        // Correction de la faute de frappe commune
        if mode == "ACPI" {
            mode = "APCI".to_string();
        }
        metadata_dict.insert("IONIZATION".to_string(), mode);
    } else {
        // S'il n'y avait rien, on s'assure que le champ existe et est vide
        metadata_dict.insert("IONIZATION".to_string(), String::new());
    }

    metadata_dict
}