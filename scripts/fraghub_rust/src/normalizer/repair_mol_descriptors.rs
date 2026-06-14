// src/normalizer/repair_mol_descriptors.rs
use std::collections::HashMap;

/// Répare la valeur 'INCHI' en s'assurant qu'elle commence par "InChI=".
pub fn repair_inchi(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    if let Some(inchi) = metadata_dict.get("INCHI") {
        if !inchi.is_empty() {
            // Remplacement via regex équivalent au re.sub de Python
            let repaired = crate::globals_vars::REPAIR_INCHI_PATTERN
                .replace(inchi, "InChI=")
                .into_owned();
            metadata_dict.insert("INCHI".to_string(), repaired);
        }
    }
    metadata_dict
}

/// Corrige les erreurs de placement entre SMILES, INCHI et INCHIKEY.
/// Équivalent natif de `repair_mol_descriptors.py`.
pub fn repair_mol_descriptors(mut metadata_dict: HashMap<String, String>) -> HashMap<String, String> {
    // Extraction des valeurs initiales (unwrap_or_default gère le cas où la clé serait absente)
    let smiles = metadata_dict.get("SMILES").cloned().unwrap_or_default();
    let inchi = metadata_dict.get("INCHI").cloned().unwrap_or_default();
    let inchikey = metadata_dict.get("INCHIKEY").cloned().unwrap_or_default();

    // --- Vérification initiale ---
    if crate::globals_vars::SMILES_PATTERN.is_match(&smiles) &&
        crate::globals_vars::INCHI_PATTERN.is_match(&inchi) &&
        crate::globals_vars::INCHIKEY_PATTERN.is_match(&inchikey)
    {
        return repair_inchi(metadata_dict);
    }

    // --- Logique de réparation croisée (Cross-Field Repair) ---
    // En Rust, on modifie directement le dictionnaire au lieu de passer par des variables mutables.

    // 1. SMILES trouvé dans le champ INCHI
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