// src/normalizer/normalize_empties.rs
use std::collections::HashMap;

/// Standardise les valeurs vides ou "nulles" du dictionnaire en chaînes vides ("").
/// 
/// Pour un développeur Python : En Rust, un `HashMap<String, String>` (l'équivalent de `Dict[str, str]`) 
/// ne permet pas qu'une valeur soit `None`. Tout est une chaîne de caractères `String`.
/// On parcourt donc les valeurs et on les remplace par `""` (String vide).
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Dictionnaire contenant les métadonnées.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire nettoyé des valeurs nulles/vides.
pub fn normalize_empties(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {

    // `.values_mut()` crée un itérateur qui permet de modifier (muter) directement 
    // les valeurs du dictionnaire sans toucher aux clés. C'est plus propre que `for (k, v) in dict.items()` en Python.
    for v in metadata_dict.values_mut() {
        if crate::globals_vars::EMPTY_PATTERN.is_match(v) {
            // L'étoile `*` déréférence la référence mutable `&mut String` pour remplacer son contenu.
            // `String::new()` crée une chaîne vide allouée dynamiquement sans garbage collector.
            *v = String::new(); 
        }
        // NB: Pas besoin de vérifier f64::NAN ici !
        // En Rust, tout est déjà String et le Regex `EMPTY_PATTERN` attrape déjà "nan".
    }

    metadata_dict // Retourne la propriété (ownership) du dictionnaire modifié.
}