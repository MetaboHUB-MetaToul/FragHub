// src/update_checker.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;
use std::collections::HashSet;
use std::fs;
use std::path::Path;
use csv::WriterBuilder;

pub fn check_for_update_processing(
    py: Python,
    spectrum_list: Vec<Spectrum>,
    output_directory: String,
    ordered_columns: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Vec<Spectrum>, bool, usize)> {

    let total_items = spectrum_list.len();

    // ⚠️ ORDRE CRITIQUE POUR L'INTERFACE VUE.JS
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items,))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, ("checking for updates:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    // 1. Lire le fichier updates.json existant
    let update_file_path = Path::new(&output_directory).join("updates.json");
    let mut splash_set: HashSet<String> = HashSet::new();
    let mut json_data = serde_json::json!({"SPLASH_LIST": {}});

    if update_file_path.exists() {
        if let Ok(file) = fs::File::open(&update_file_path) {
            if let Ok(parsed) = serde_json::from_reader::<_, serde_json::Value>(file) {
                json_data = parsed;
                if let Some(splash_list) = json_data.get("SPLASH_LIST").and_then(|v| v.as_object()) {
                    for key in splash_list.keys() {
                        splash_set.insert(key.clone()); // On stocke les SPLASH connus dans un Hash ultra-rapide
                    }
                }
            }
        }
    }

    // --- CORRECTION : Utilisation d'un HashSet pour une recherche en O(1) ---
    let mut indices_to_keep: HashSet<usize> = HashSet::new();
    let mut indices_to_delete = Vec::new();
    let mut new_splashes = Vec::new();
    let mut processed = 0;

    // 2. Parcourir les spectres
    for (i, spec) in spectrum_list.iter().enumerate() {
        let splash = spec.metadata.get("SPLASH").cloned().unwrap_or_default();

        if !splash.is_empty() && splash_set.contains(&splash) {
            indices_to_delete.push(i); // Déjà vu -> on supprime
        } else {
            // --- CORRECTION : Utilisation de .insert() au lieu de .push() ---
            indices_to_keep.insert(i); // Nouveau -> on garde
            if !splash.is_empty() {
                new_splashes.push(splash);
            }
        }

        processed += 1;
        if processed % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }

    // 3. Écrire les doublons supprimés dans le CSV
    if !indices_to_delete.is_empty() {
        let deleted_dir = Path::new(&output_directory).join("DELETED_SPECTRUMS");
        fs::create_dir_all(&deleted_dir)?;
        let file_path = deleted_dir.join("previously_cleaned.csv");

        let mut wtr = WriterBuilder::new()
            .delimiter(b'\t')
            .quote(b'"')
            .from_path(file_path)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        let mut header = ordered_columns.clone();
        header.push("DELETION_REASON".to_string());
        wtr.write_record(&header).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        for &idx in &indices_to_delete {
            let spec = &spectrum_list[idx];
            let mut record: Vec<String> = Vec::with_capacity(ordered_columns.len() + 1);

            for col in &ordered_columns {
                record.push(spec.metadata.get(col).cloned().unwrap_or_default());
            }
            record.push("spectrum deleted because already processed in a previous run.".to_string());
            wtr.write_record(&record).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        }
        wtr.flush()?;
    }

    // 4. Mettre à jour le fichier JSON
    let update = !new_splashes.is_empty();
    if update {
        if let Some(obj) = json_data.get_mut("SPLASH_LIST").and_then(|v| v.as_object_mut()) {
            for s in new_splashes {
                obj.insert(s, serde_json::json!(true));
            }
        } else {
            let mut new_obj = serde_json::Map::new();
            for s in new_splashes {
                new_obj.insert(s, serde_json::json!(true));
            }
            json_data["SPLASH_LIST"] = serde_json::Value::Object(new_obj);
        }

        let file = std::fs::File::create(&update_file_path).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        serde_json::to_writer_pretty(file, &json_data).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
    }

    // 5. Générer la liste finale (Sera maintenant quasi instantané)
    let mut final_list = Vec::with_capacity(indices_to_keep.len());
    let mut current_idx = 0;
    for spec in spectrum_list.into_iter() {
        if indices_to_keep.contains(&current_idx) {
            final_list.push(spec);
        }
        current_idx += 1;
    }

    // ⚠️ GARANTIE DU 100%
    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    // On renvoie la nouvelle liste, le booléen (y a-t-il eu une MAJ ?), et le nombre de supprimés
    Ok((final_list, update, indices_to_delete.len()))
}