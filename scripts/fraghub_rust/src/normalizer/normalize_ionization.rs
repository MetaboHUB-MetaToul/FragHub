// src/normalizer/normalize_ionization.rs
use std::collections::HashMap;

/// Normalise le mode d'ionisation en lisant IONIZATION ou INSTRUMENTTYPE.
///
/// Pour un développeur Python : Cette fonction illustre le "Pattern Matching" avec `if let`.
/// C'est une façon très élégante de dire "Si ça contient quelque chose, extrait-le et exécute ce bloc".
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec l'ionisation standardisée.
pub fn normalize_ionization(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let mut found_mode: Option<String> = None;

    // 1. Chercher d'abord dans IONIZATION
    // On extrait la valeur. Si elle n'existe pas, le bloc est ignoré sans générer d'erreur KeyError.
    if let Some(ion) = metadata_dict.get("IONIZATION") {
        if let Some(caps) = crate::globals_vars::IONIZATION_MODE_PATTERN.captures(ion) {
            // Les groupes de l'expression régulière (capture) retournent aussi des Option.
            if let Some(m) = caps.get(1) {
                // On met en majuscules pour garantir la correction (ex: "apci" -> "APCI").
                found_mode = Some(m.as_str().to_uppercase());
            }
        }
    }

    // 2. Si rien n'est trouvé, chercher dans INSTRUMENTTYPE
    // `.is_none()` équivaut à `found_mode is None` en Python.
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
    // `mut mode` permet de modifier la variable locale `mode` extraite du `Some()`.
    if let Some(mut mode) = found_mode {
        // Correction de la faute de frappe commune "ACPI" au lieu de "APCI"
        if mode == "ACPI" {
            mode = "APCI".to_string(); // Doit être une String, pas un &str
        }
        metadata_dict.insert("IONIZATION".to_string(), mode);
    } else {
        // S'il n'y avait rien, on s'assure que le champ existe et est vide.
        metadata_dict.insert("IONIZATION".to_string(), String::new());
    }

    metadata_dict
}