// src/duplicatas_remover.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use std::collections::{HashMap, HashSet};
use std::fs;
use std::path::Path;
use csv::WriterBuilder;

#[pyfunction]
#[pyo3(signature = (spectrum_list, output_directory, ordered_columns, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn remove_duplicatas_processing<'py>(
    py: Python<'py>,
    spectrum_list: Bound<'py, PyList>,
    output_directory: String,
    ordered_columns: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Bound<'py, PyList>, usize)> {

    let total_items = spectrum_list.len();

    // ⚠️ ORDRE CRITIQUE POUR L'INTERFACE VUE.JS
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items,))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Removing duplicates:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let mut best_indices: HashMap<(String, String), (usize, usize)> = HashMap::new();
    let mut empty_inchi_indices: Vec<usize> = Vec::new();

    let mut processed = 0;

    for i in 0..total_items {
        let item = spectrum_list.get_item(i).unwrap();
        let dict = item.downcast::<PyDict>()?;

        let mut row_size = 0;
        for col in &ordered_columns {
            if let Ok(Some(val)) = dict.get_item(col) {
                if let Ok(val_str) = val.downcast::<PyString>() {
                    if let Ok(s) = val_str.to_str() { row_size += s.chars().count(); }
                } else if let Ok(val_str) = val.str() {
                    if let Ok(s) = val_str.to_str() { row_size += s.chars().count(); }
                }
            }
        }

        let splash = if let Ok(Some(s)) = dict.get_item("SPLASH") {
            if let Ok(s_str) = s.str() { s_str.to_str().unwrap_or("").to_string() } else { String::new() }
        } else { String::new() };

        let inchikey = if let Ok(Some(inch)) = dict.get_item("INCHIKEY") {
            if let Ok(inch_str) = inch.str() { inch_str.to_str().unwrap_or("").trim().to_string() } else { String::new() }
        } else { String::new() };

        if inchikey.is_empty() || inchikey.to_lowercase() == "nan" || inchikey.to_lowercase() == "none" {
            empty_inchi_indices.push(i);
        } else {
            let key = (splash, inchikey);
            if let Some(&(_, best_size)) = best_indices.get(&key) {
                if row_size > best_size {
                    best_indices.insert(key, (i, row_size));
                }
            } else {
                best_indices.insert(key, (i, row_size));
            }
        }

        processed += 1;
        if processed % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }

    let mut indices_to_keep: HashSet<usize> = HashSet::new();
    for &idx in &empty_inchi_indices { indices_to_keep.insert(idx); }
    for &(idx, _) in best_indices.values() { indices_to_keep.insert(idx); }

    let mut indices_to_delete: Vec<usize> = Vec::new();
    for i in 0..total_items {
        if !indices_to_keep.contains(&i) {
            indices_to_delete.push(i);
        }
    }

    if !indices_to_delete.is_empty() {
        let deleted_dir = Path::new(&output_directory).join("DELETED_SPECTRUMS");
        fs::create_dir_all(&deleted_dir)?;
        let file_path = deleted_dir.join("duplicatas_removed.csv");

        let mut wtr = WriterBuilder::new()
            .delimiter(b'\t')
            .quote(b'"')
            .from_path(file_path)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        let mut header = ordered_columns.clone();
        header.push("DELETION_REASON".to_string());
        wtr.write_record(&header).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        for &idx in &indices_to_delete {
            let item = spectrum_list.get_item(idx).unwrap();
            let dict = item.downcast::<PyDict>()?;
            let mut record: Vec<String> = Vec::with_capacity(ordered_columns.len() + 1);

            for col in &ordered_columns {
                if let Ok(Some(val)) = dict.get_item(col) {
                    if let Ok(val_str) = val.str() {
                        if let Ok(s) = val_str.to_str() {
                            record.push(s.to_string());
                            continue;
                        }
                    }
                }
                record.push(String::new());
            }
            record.push("spectrum deleted because it's a duplicate (SPLASH + INCHIKEY)".to_string());
            wtr.write_record(&record).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        }
        wtr.flush()?;
    }

    let final_list = PyList::empty_bound(py);
    for i in 0..total_items {
        if indices_to_keep.contains(&i) {
            final_list.append(spectrum_list.get_item(i).unwrap())?;
        }
    }

    // ⚠️ GARANTIE DU 100% POUR CLÔTURER L'INTERFACE PROPREMENT
    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    Ok((final_list, indices_to_delete.len()))
}