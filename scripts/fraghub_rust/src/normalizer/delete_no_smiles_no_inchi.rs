// src/normalizer/delete_no_smiles_no_inchi.rs
use std::collections::HashMap;

/// Supprime un spectre si les métadonnées n'ont aucun des trois identifiants chimiques.
///
/// Pour un développeur Python : En Rust, pour indiquer qu'une fonction peut échouer ou retourner "Rien", 
/// on encapsule le retour dans un enum `Option<T>`. On renvoie `Some(valeur)` si c'est valide, et `None` sinon.
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Dictionnaire des métadonnées.
/// * `deletion_reason` (&mut Option<String>) : Pointeur mutable pour indiquer la suppression.
///
/// # Returns
/// * `Option<HashMap<String, String>>` : `Some(dict)` si un identifiant existe, sinon `None`.
pub fn delete_no_smiles_no_inchi_no_inchikey(
    metadata_dict: HashMap<String, String>,
    deletion_reason: &mut Option<String>
) -> Option<HashMap<String, String>> {

    // On vérifie si les clés existent ET si elles ne sont pas vides.
    // `.map_or(false, closure)` : si le champ n'existe pas, on renvoie `false`. 
    // Sinon, on applique la fonction anonyme `|s| !s.is_empty()` pour vérifier si le texte n'est pas vide.
    let has_smiles = metadata_dict.get("SMILES").map_or(false, |s| !s.is_empty());
    let has_inchi = metadata_dict.get("INCHI").map_or(false, |s| !s.is_empty());
    let has_inchikey = metadata_dict.get("INCHIKEY").map_or(false, |s| !s.is_empty());

    if !has_smiles && !has_inchi && !has_inchikey {
        // On modifie la variable pointée par `deletion_reason` pour garder une trace de la suppression.
        *deletion_reason = Some("spectrum deleted because it has neither inchi nor smiles nor inchikey".to_string());
        return None; // Le dictionnaire disparaît ici, sa mémoire est libérée.
    }

    // Si au moins un identifiant est présent, on "emballe" le dictionnaire valide dans `Some`.
    Some(metadata_dict)
}