// src/convertors/keys_convertor.rs

use std::collections::HashMap;

/// Convertit les clés du dictionnaire de métadonnées selon le dictionnaire de correspondance fourni.
///
/// Pour un développeur Python : En Python, on modifierait parfois le dictionnaire pendant l'itération,
/// ce qui peut causer des erreurs. En Rust, on itère sur les clés de `metadata_dict` 
/// (ce qui le "consomme") et on peuple un tout nouveau dictionnaire `converted`.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire source.
/// * `keys_dict` (HashMap<String, String>) : Le dictionnaire de traduction des clés.
/// * `keys_list` (Vec<String>) : La liste complète des clés à conserver impérativement.
///
/// # Returns
/// * `HashMap<String, String>` : Le nouveau dictionnaire avec les clés standardisées.
pub fn convert_keys(
    metadata_dict: HashMap<String, String>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>
) -> HashMap<String, String> {

    // On alloue un nouveau dictionnaire vide.
    let mut converted: HashMap<String, String> = HashMap::new();

    // Boucle for qui "consomme" le dictionnaire d'entrée (Ownership)
    for (key, val) in metadata_dict {
        let lower_key = key.to_lowercase();

        // `get` sur `keys_dict` renvoie une référence. Si elle existe, on l'utilise.
        if let Some(mapped_key) = keys_dict.get(&lower_key) {
            // Vérifie que la clé fait partie des clés autorisées (keys_list).
            if keys_list.contains(mapped_key) {
                // On doit `.clone()` la clé car `converted` a besoin d'en être le propriétaire.
                converted.insert(mapped_key.clone(), val);
            }
        }
    }

    // Après la conversion initiale, on ajoute les clés manquantes avec une valeur vide.
    for key in keys_list {
        // L'API `.entry()` de HashMap est très puissante : elle cherche la clé `key`.
        // Si elle n'existe pas, `.or_insert_with` la crée avec la valeur retournée par la closure.
        converted.entry(key).or_insert_with(|| String::from(""));
    }

    converted
}