// src/normalizer/repair_mol_descriptors.rs
use std::collections::HashMap;

/// Répare la valeur 'INCHI' en s'assurant qu'elle commence par "InChI=".
///
/// Pour un développeur Python : Cette fonction remplace un bloc de texte avec une expression régulière.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec le champ INCHI réparé.
pub fn repair_inchi(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    // `if let Some(inchi)` gère proprement le cas où la clé "INCHI" n'existerait pas dans le dictionnaire.
    // `.get()` retourne un `Option<&String>`, on extrait donc une référence vers le texte.
    if let Some(inchi) = metadata_dict.get("INCHI") {
        if !inchi.is_empty() {
            // Remplacement via regex équivalent au `re.sub` de Python.
            // `.into_owned()` convertit le type `Cow<str>` (Copy-On-Write) retourné par `replace` 
            // en une vraie `String` indépendante. C'est très optimisé en Rust.
            let repaired = crate::globals_vars::REPAIR_INCHI_PATTERN
                .replace(inchi, "InChI=")
                .into_owned();
                
            // `.insert()` remplace l'ancienne valeur si la clé existe déjà.
            // En Rust, "INCHI" est une vue statique (`&str`), on doit appeler `.to_string()` pour l'allouer sur le tas (`String`).
            metadata_dict.insert("INCHI".to_string(), repaired);
        }
    }
    metadata_dict
}

/// Corrige les erreurs de placement entre SMILES, INCHI et INCHIKEY.
/// 
/// Pour un développeur Python : Remplace les logiques de déplacement de champs. Au lieu de copier 
/// `dict["A"] = dict["B"]`, on clone (`.clone()`) car Rust interdit à deux variables d'être propriétaires
/// de la même chaîne de caractères en mémoire.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Le dictionnaire des métadonnées du spectre.
///
/// # Returns
/// * `HashMap<String, String>` : Le dictionnaire avec les descripteurs moléculaires aux bons endroits.
pub fn repair_mol_descriptors(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    // `.cloned()` crée une vraie copie de la String pour nous permettre de la manipuler.
    // `.unwrap_or_default()` renvoie une chaîne vide `""` si la clé n'existait pas (au lieu de crasher).
    let smiles = metadata_dict.get("SMILES").cloned().unwrap_or_default();
    let inchi = metadata_dict.get("INCHI").cloned().unwrap_or_default();
    let inchikey = metadata_dict.get("INCHIKEY").cloned().unwrap_or_default();

    // --- Vérification initiale ---
    if crate::globals_vars::SMILES_PATTERN.is_match(&smiles) &&
        crate::globals_vars::INCHI_PATTERN.is_match(&inchi) &&
        crate::globals_vars::INCHIKEY_PATTERN.is_match(&inchikey)
    {
        return repair_inchi(metadata_dict); // Sortie prématurée si tout est bon.
    }

    // --- Logique de réparation croisée (Cross-Field Repair) ---
    // En Rust, on modifie directement le dictionnaire via `.insert()` au lieu de passer par l'opérateur `[]` de Python.

    // 1. SMILES trouvé dans le champ INCHI
    // `&inchi` emprunte la variable pour que l'expression régulière la lise sans la détruire.
    if crate::globals_vars::SMILES_PATTERN.is_match(&inchi) &&
        !crate::globals_vars::INCHI_PATTERN.is_match(&inchi) &&
        !crate::globals_vars::INCHIKEY_PATTERN.is_match(&inchi)
    {
        metadata_dict.insert("SMILES".to_string(), inchi.clone());
        metadata_dict.insert("INCHI".to_string(), String::new());
    }

    // 2. SMILES trouvé dans le champ INCHIKEY
    if crate::globals_vars::SMILES_PATTERN.is_match(&inchikey) &&
        !crate::globals_vars::INCHI_PATTERN.is_match(&inchikey) &&
        !crate::globals_vars::INCHIKEY_PATTERN.is_match(&inchikey)
    {
        metadata_dict.insert("SMILES".to_string(), inchikey.clone());
        metadata_dict.insert("INCHIKEY".to_string(), String::new());
    }

    // 3. INCHI trouvé dans le champ SMILES
    if crate::globals_vars::INCHI_PATTERN.is_match(&smiles) {
        metadata_dict.insert("INCHI".to_string(), smiles.clone());
        metadata_dict.insert("SMILES".to_string(), String::new());
    }

    // 4. INCHI trouvé dans le champ INCHIKEY
    if crate::globals_vars::INCHI_PATTERN.is_match(&inchikey) {
        metadata_dict.insert("INCHI".to_string(), inchikey.clone());
        metadata_dict.insert("INCHIKEY".to_string(), String::new());
    }

    // 5. INCHIKEY trouvé dans le champ INCHI
    if crate::globals_vars::INCHIKEY_PATTERN.is_match(&inchi) {
        metadata_dict.insert("INCHIKEY".to_string(), inchi.clone());
        metadata_dict.insert("INCHI".to_string(), String::new());
    }

    // 6. INCHIKEY trouvé dans le champ SMILES
    if crate::globals_vars::INCHIKEY_PATTERN.is_match(&smiles) {
        metadata_dict.insert("INCHIKEY".to_string(), smiles.clone());
        metadata_dict.insert("SMILES".to_string(), String::new());
    }

    // Étape finale : on sécurise le préfixe de l'InChI
    repair_inchi(metadata_dict)
}