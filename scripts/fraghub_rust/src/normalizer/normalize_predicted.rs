use std::collections::HashMap;

/// Détecte si le spectre est "in silico" (prédit par ordinateur).
///
/// Pour un développeur Python : La logique if/else if est stricte en Rust.
/// On doit comparer des `String` en utilisant `==` et `.to_lowercase()`.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec PREDICTED à "true" ou "false".
pub fn normalize_predicted(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let predicted = metadata_dict.get("PREDICTED").cloned().unwrap_or_default();
    if predicted.to_lowercase() == "false" {
        return metadata_dict;
    }

    let comment = metadata_dict.get("COMMENT").cloned().unwrap_or_default();
    let filename = metadata_dict.get("FILENAME").cloned().unwrap_or_default();
    let name = metadata_dict.get("NAME").cloned().unwrap_or_default();

    let mut is_predicted = false;
    
    // Le `||` est le OR logique (équivalent à `or` en Python).
    if crate::globals_vars::IN_SILICO_PATTERN.is_match(&comment) || predicted.to_lowercase() == "true" {
        is_predicted = true;
    } else if !filename.contains("MSMS_Public") {
        // `format!` est l'équivalent parfait des f-strings Python : f"{filename} {name}"
        let combined = format!("{} {}", filename, name);
        if crate::globals_vars::IN_SILICO_PATTERN.is_match(&combined) {
            is_predicted = true;
        }
    }

    // L'expression `if condition { A } else { B }` peut être utilisée pour retourner une valeur directement.
    // C'est l'équivalent de `A if condition else B` en Python.
    metadata_dict.insert("PREDICTED".to_string(), if is_predicted { "true".to_string() } else { "false".to_string() });
    
    metadata_dict
}