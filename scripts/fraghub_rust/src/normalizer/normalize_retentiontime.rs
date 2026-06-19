use std::collections::HashMap;

/// Convertit le temps de rétention en minutes (float) peu importe l'unité d'origine.
///
/// Pour un développeur Python : Observez le mot-clé `match`. C'est le cousin très puissant
/// du `switch`/`case` ou du récent `match` en Python 3.10. Le compilateur Rust nous obligera
/// TOUJOURS à traiter tous les cas possibles (exhaustivité), d'où le `_ =>` (le cas "else" par défaut).
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec RT normalisé en minutes.
pub fn normalize_retention_time(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    let rt = metadata_dict.get("RT").cloned().unwrap_or_default();

    if let Some(caps) = crate::globals_vars::RETENTION_TIME_PATTERN.captures(&rt) {
        if let Some(time_match) = caps.get(1) {
            // `.parse::<f64>()` remplace le `float(valeur)` de Python. 
            // Si la conversion réussit (`Ok`), on rentre dans le bloc.
            if let Ok(time_val) = time_match.as_str().parse::<f64>() {
                // On récupère l'unité (groupe 2 de la regex) ou "" par défaut
                let unit = caps.get(2).map(|m| m.as_str().to_lowercase()).unwrap_or_default();
                
                // Le `match` (pattern matching) pour la conversion d'unités
                let final_rt = match unit.as_str() {
                    "m" | "min" | "minute" | "minutes" | "" => time_val, // Déjà en minutes
                    "s" | "sec" | "second" | "seconds" => time_val / 60.0, // Secondes -> Minutes
                    "ms" | "millisecond" | "milliseconds" => time_val / 60000.0, // Millisecondes -> Minutes
                    _ => time_val, // Par sécurité (le compilateur l'exige)
                };
                
                metadata_dict.insert("RT".to_string(), final_rt.to_string());
            }
        }
    }
    metadata_dict
}