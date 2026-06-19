// src/normalizer/check_for_bad_adduct.rs
use std::collections::HashMap;

/// Vérifie que l'adduct est cohérent avec le mode d'ionisation.
///
/// Pour un développeur Python : Retourne `Option<HashMap>` pour propager une suppression silencieusement.
/// Le `deletion_reason` est passé par `&mut` pour permettre à la fonction de modifier la raison 
/// visible par le rapporteur final en cas de suppression (renvoi de `None`).
///
/// # Arguments
/// * `metadata_dict` (HashMap<String, String>) : Dictionnaire contenant les métadonnées.
/// * `deletion_reason` (&mut Option<String>) : Pointeur mutable pour stocker la raison de suppression.
/// * `context` (&NormalizerContext) : Dictionnaires de référence pour les adducts.
///
/// # Returns
/// * `Option<HashMap<String, String>>` : Dictionnaire valide ou `None` si incohérent.
pub fn check_for_bad_adduct(
    mut metadata_dict: HashMap<String, String>,
    deletion_reason: &mut Option<String>,
    context: &super::NormalizerContext
) -> Option<HashMap<String, String>> {

    let mut adduct = metadata_dict.get("PRECURSORTYPE").cloned().unwrap_or_default();
    let ion_mode = metadata_dict.get("IONMODE").cloned().unwrap_or_default();
    let predicted = metadata_dict.get("PREDICTED").cloned().unwrap_or_default();
    let instrument_type = metadata_dict.get("INSTRUMENTTYPE").cloned().unwrap_or_default();

    // 1. Gérer l'adduct manquant si "PREDICTED" est vrai
    if predicted == "true" && adduct.is_empty() {
        if ion_mode == "positive" {
            adduct = "[M+H]+".to_string();
            metadata_dict.insert("PRECURSORTYPE".to_string(), adduct.clone());
        } else if ion_mode == "negative" {
            adduct = "[M-H]-".to_string();
            metadata_dict.insert("PRECURSORTYPE".to_string(), adduct.clone());
        }
    }

    // 2. Gérer les instruments spécifiques (ex: GC-MS)
    if crate::globals_vars::GC_PATTERN.is_match(&instrument_type) && adduct.is_empty() {
        return Some(metadata_dict); // OK, on garde
    }

    // 3. Gérer la forme courte "M"
    if adduct == "M" {
        if ion_mode == "positive" {
            adduct = "[M]+".to_string();
            metadata_dict.insert("PRECURSORTYPE".to_string(), adduct.clone());
            return Some(metadata_dict);
        } else if ion_mode == "negative" {
            adduct = "[M]-".to_string();
            metadata_dict.insert("PRECURSORTYPE".to_string(), adduct.clone());
            return Some(metadata_dict);
        }
    }

    // 4. Valider le format de l'adduct
    if !crate::globals_vars::IS_ADDUCT_PATTERN.is_match(&adduct) {
        *deletion_reason = Some("spectrum deleted because its adduct field is empty or the value entered is not an adduct".to_string());
        return None; // Suppression du spectre
    }

    // 5. Valider la cohérence Adduct / Ion Mode grâce aux dictionnaires en RAM (`context.adduct_massdiff_neg`)
    if ion_mode == "positive" {
        if context.adduct_massdiff_neg.contains_key(&adduct) {
            *deletion_reason = Some("spectrum deleted because the adduct corresponds to the wrong ionization mode (neg adduct in pos ionmode).".to_string());
            return None;
        }
    } else if ion_mode == "negative" {
        if context.adduct_massdiff_pos.contains_key(&adduct) {
            *deletion_reason = Some("spectrum deleted because the adduct corresponds to the wrong ionization mode (pos adduct in neg ionmode).".to_string());
            return None;
        }
    }

    Some(metadata_dict) // Tout est valide, on renvoie le spectre
}