// src/normalizer/normalize_instruments_and_resolution.rs
use std::collections::HashMap;
use regex::Regex;
use once_cell::sync::Lazy;

/// Nettoie les informations de base des instruments.
/// 
/// Pour un développeur Python : L'utilisation de `Lazy::new()` permet de compiler les regex
/// une seule fois au premier appel (équivalent à compiler ses regex globalement en Python), 
/// évitant de tuer les performances en les recompilant à chaque passage.
fn apply_common_cleaning(mut s: String) -> String {
    s = s.replace("-tof", "tof");
    s = s.replace("q-", "q");
    s = s.replace("q exactive", " qexactive ");
    s = s.replace("applied biosystems", " sciex ");
    s = s.replace(" ab ", " sciex ");
    s = s.replace("sciex", " sciex ");

    static TRIPLE_TOF: Lazy<Regex> = Lazy::new(|| Regex::new(r"triple[- ]?tof").unwrap());
    s = TRIPLE_TOF.replace_all(&s, " qqq ").into_owned();

    static TRIPLE_QUAD: Lazy<Regex> = Lazy::new(|| Regex::new(r"triple[- ]?quad").unwrap());
    s = TRIPLE_QUAD.replace_all(&s, " qqq ").into_owned();

    static UPLC: Lazy<Regex> = Lazy::new(|| Regex::new(r".{3} uplc .{3}").unwrap());
    s = UPLC.replace_all(&s, " ").into_owned();

    s
}

/// Fusionne et nettoie divers champs (INSTRUMENT, INSTRUMENTTYPE, COMMENT)
fn clean_spectrum_instrument_info(metadata_dict: &HashMap<String, String>) -> String {
    let instrument = apply_common_cleaning(metadata_dict.get("INSTRUMENT").cloned().unwrap_or_default().to_lowercase());

    let mut instrument_type = metadata_dict.get("INSTRUMENTTYPE").cloned().unwrap_or_default().to_lowercase();
    instrument_type = instrument_type.replace("-", " "); // Spécifique au type
    instrument_type = apply_common_cleaning(instrument_type);

    let mut comment = metadata_dict.get("COMMENT").cloned().unwrap_or_default().to_lowercase();
    comment = comment.replace("-", " "); // Spécifique au commentaire
    comment = apply_common_cleaning(comment);

    let infos = format!("{} {} {}", instrument, instrument_type, comment);

    // Supprime tout ce qui n'est pas alphanumérique, espace ou tiret
    static CLEAN_CHARS: Lazy<Regex> = Lazy::new(|| Regex::new(r"[^-\w\s]").unwrap());
    let cleaned = CLEAN_CHARS.replace_all(&infos, " ").into_owned();

    // `.split_whitespace().collect::<Vec<&str>>().join(" ")` enlève les doubles espaces.
    cleaned.split_whitespace().collect::<Vec<&str>>().join(" ")
}

// Remplace la lenteur du regex rf"(\b|^|$){key}(\b|^|$)" de Python par une vérification native ultra-rapide
// Python utilise un moteur Regex basé sur le langage C, mais les appels répétés en Python coûtent cher.
// En Rust, analyser directement les octets (`bytes`) est immensément plus rapide.
fn is_word_char(b: u8) -> bool { b.is_ascii_alphanumeric() || b == b'_' }

fn contains_word(text: &str, word: &str) -> bool {
    if word.is_empty() { return false; }
    let text_bytes = text.as_bytes(); // Travaille directement sur les octets ASCII
    let word_bytes = word.as_bytes();
    let word_len = word_bytes.len();

    let mut start = 0;
    while let Some(pos) = text[start..].find(word) {
        let actual_pos = start + pos;
        let end_pos = actual_pos + word_len;

        // Vérifie les limites du mot (boundaries)
        let is_left_boundary = actual_pos == 0 || !is_word_char(text_bytes[actual_pos - 1]);
        let is_right_boundary = end_pos == text_bytes.len() || !is_word_char(text_bytes[end_pos]);

        if is_left_boundary && is_right_boundary { return true; }
        start = actual_pos + 1;
    }
    false
}

/// Parcourt l'arborescence (arbre JSON de configuration) pour résoudre l'instrument.
/// La syntaxe `<'a>` décrit une "Lifetime" (durée de vie). Elle indique au compilateur que les 
/// références retournées par la fonction vivront aussi longtemps que l'arbre `tree` passé en paramètre.
fn search_level<'a>(tree: &'a serde_json::Value, infos: &str) -> Option<(&'a String, &'a serde_json::Value)> {
    if let Some(map) = tree.as_object() {
        for (key, next_level) in map {
            if contains_word(infos, key) { return Some((key, next_level)); }
        }
    }
    None
}

/// Identifie avec précision le modèle d'instrument, le type d'ionisation et la résolution.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
/// * `context` (&super::NormalizerContext) : Contexte contenant l'arbre de décision JSON des instruments.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire mis à jour avec INSTRUMENT, INSTRUMENTTYPE, RESOLUTION.
pub fn normalize_instruments_and_resolution(mut metadata_dict: HashMap<String, String>, context: &super::NormalizerContext) -> HashMap<String, String> {
    let instrument_infos = clean_spectrum_instrument_info(&metadata_dict);
    let infos = format!(". {} .", instrument_infos);

    let mut current_level = &context.instrument_tree;
    let mut tree_levels = Vec::new();

    // On descend les 5 niveaux (Marque, Modèle, Type Spectre, Type Instrument, Ionisation)
    for _ in 0..5 {
        if let Some((key, next)) = search_level(current_level, &infos) {
            tree_levels.push(key.clone());
            current_level = next;
        } else {
            return metadata_dict; // Si on ne trouve pas, on arrête et on renvoie le dico intact
        }
    }

    if tree_levels.len() == 5 {
        metadata_dict.insert("TREE_MARQUE".to_string(), tree_levels[0].clone());
        metadata_dict.insert("TREE_MODELE".to_string(), tree_levels[1].clone());
        metadata_dict.insert("TREE_SPECTYPE".to_string(), tree_levels[2].clone());
        metadata_dict.insert("TREE_INSTYPE".to_string(), tree_levels[3].clone());
        metadata_dict.insert("TREE_IONI".to_string(), tree_levels[4].clone());
    }

    // Niveau 6 : Résolution
    if let Some(res_level) = current_level.as_object() {
        let resolution = if res_level.contains_key("high") { "high" }
        else if res_level.contains_key("low") { "low" }
        else { "unknown" };

        // Chaînage de méthodes sécurisé via `and_then` pour naviguer dans l'objet JSON.
        if let Some(solution_str) = res_level.get(resolution).and_then(|r| r.get("SOLUTION")).and_then(|s| s.as_str()) {
            let parts: Vec<&str> = solution_str.split(',').collect();
            if parts.len() >= 3 {
                metadata_dict.insert("INSTRUMENT".to_string(), parts[0].trim().to_string());
                metadata_dict.insert("INSTRUMENTTYPE".to_string(), parts[1].trim().to_string());
                metadata_dict.insert("RESOLUTION".to_string(), parts[2].trim().to_string());

                let inst_type_parts: Vec<&str> = parts[1].split('-').collect();
                if inst_type_parts.len() >= 2 {
                    metadata_dict.insert("IONIZATION".to_string(), inst_type_parts[1].trim().to_string());
                }
            }
        }
    }

    metadata_dict
}