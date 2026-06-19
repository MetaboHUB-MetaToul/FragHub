use std::collections::HashMap;

/// Standardise le niveau MS (MS1, MS2, MS3, etc.).
///
/// Pour un développeur Python : L'utilisation de `.find_iter()` sur une regex en Rust renvoie un itérateur.
/// On utilise ensuite `.map(|m| m.as_str())` pour transformer chaque `Match` en simple texte `&str`,
/// et enfin `.collect()` pour rassembler tout ça dans un vecteur (`Vec<&str>`). C'est l'équivalent
/// d'une liste en compréhension en Python : `[m.group() for m in pattern.finditer(text)]`.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec le niveau MS standardisé.
pub fn normalize_ms_level(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let ms_level = metadata_dict.get("MSLEVEL").cloned().unwrap_or_default();

    if !ms_level.is_empty() {
        // Extraction de tous les niveaux MS mentionnés (ex: "MS2/MS3" -> ["2", "3"])
        let matched_levels: Vec<&str> = crate::globals_vars::MS_LEVEL_PATTERN
            .find_iter(&ms_level)
            .map(|m| m.as_str())
            .collect();

        // Si on a trouvé exactement 1 niveau, on l'utilise.
        if matched_levels.len() == 1 {
            metadata_dict.insert("MSLEVEL".to_string(), matched_levels[0].to_string());
        } 
        // Si on en a trouvé plusieurs, on fait un format combiné (ex: "2-3")
        else if matched_levels.len() >= 2 {
            // `format!` est l'équivalent de f"{matched_levels[0]}-{matched_levels[1]}"
            metadata_dict.insert("MSLEVEL".to_string(), format!("{}-{}", matched_levels[0], matched_levels[1]));
        } 
        // Par défaut, si rien ne match (ou MS inconnu), on suppose MS2.
        else {
            metadata_dict.insert("MSLEVEL".to_string(), "2".to_string());
        }
    } else {
        // Par défaut, on suppose MS2 si le champ est vide.
        metadata_dict.insert("MSLEVEL".to_string(), "2".to_string());
    }

    metadata_dict
}