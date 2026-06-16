// src/ontologies_completion.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;

pub fn ontologies_completion_processing(
    py: Python,
    mut spectrum_list: Vec<Spectrum>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<Spectrum>> {

    // --- Step 1: Initialization ---
    if let Some(cb) = &prefix_callback { cb.call1(py, ("updating ontologies (Rust):",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    // On sauvegarde l'ordre des colonnes


    // Contrairement à votre Python qui simulait la progression avec le nombre de clés uniques,
    // on va faire une vraie progression fluide basée sur le nombre total de lignes.
    let total_items = spectrum_list.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    // --- Step 2: Récupération de ontologies_df depuis Rust Global State ---
    let state = crate::global_state::STATE.read().unwrap();
    let ont_dict = &state.ontologies_datas;

    let columns_to_update = [
        "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS",
        "NPCLASS_PATHWAY", "NPCLASS_SUPERCLASS", "NPCLASS_CLASS"
    ];

    let mut processed = 0;

    // --- Step 3: Boucle de mise à jour (In-place) ---
    for spec in spectrum_list.iter_mut() {

        // Par défaut, on initialise tout à "NOT FOUND" comme dans votre code Python
        for col in columns_to_update {
            spec.metadata.insert(col.to_string(), "NOT FOUND".to_string());
        }

        // Si on a un INCHIKEY valide, on cherche dans la base de données
        let inchikey = spec.metadata.get("INCHIKEY").cloned().unwrap_or_default();

        if !inchikey.is_empty() && inchikey.to_lowercase() != "nan" {
            if let Some(ont_row) = ont_dict.get(&inchikey) {
                for col in columns_to_update {
                    if let Some(new_val) = ont_row.get(col) {
                        if !new_val.trim().is_empty() && new_val.to_lowercase() != "nan" {
                            spec.metadata.insert(col.to_string(), new_val.clone());
                        }
                    }
                }
            }
        }

        processed += 1;
        // Barre de progression
        if processed % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }

    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    Ok(spectrum_list)
}