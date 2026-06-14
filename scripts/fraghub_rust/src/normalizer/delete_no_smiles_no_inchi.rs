// src/normalizer/delete_no_smiles_no_inchi.rs
use std::collections::HashMap;

/// Supprime un spectre si les métadonnées n'ont aucun des trois identifiants chimiques.
/// Renvoie None si le spectre doit être supprimé, sinon renvoie Some(metadata_dict).
pub fn delete_no_smiles_no_inchi_no_inchikey(
    metadata_dict: HashMap<String, String>,
    deletion_reason: &mut Option<String>
) -> Option<HashMap<String, String>> {

    // On vérifie si les clés existent ET si elles ne sont pas vides
    let has_smiles = metadata_dict.get("SMILES").map_or(false, |s| !s.is_empty());
    let has_inchi = metadata_dict.get("INCHI").map_or(false, |s| !s.is_empty());
    let has_inchikey = metadata_dict.get("INCHIKEY").map_or(false, |s| !s.is_empty());

    if !has_smiles && !has_inchi && !has_inchikey {
        // On enregistre la raison de la suppression pour le rapport final
        *deletion_reason = Some("spectrum deleted because it has neither inchi nor smiles nor inchikey".to_string());
        return None;
    }

    // Si au moins un identifiant est présent, on garde le dictionnaire
    Some(metadata_dict)
}