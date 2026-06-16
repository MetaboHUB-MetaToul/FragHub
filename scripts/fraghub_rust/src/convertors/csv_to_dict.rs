// src/convertors/csv_to_dict.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;
use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader};

// Import du générateur de hash
use crate::convertors::loaders::generate_file_hash;

// 1. Détection du séparateur (comme dans votre Python)
fn detect_separator(file_path: &str) -> u8 {
    if let Ok(file) = File::open(file_path) {
        let mut reader = BufReader::new(file);
        let mut first_line = String::new();
        if reader.read_line(&mut first_line).is_ok() {
            let tab_count = first_line.matches('\t').count();
            let semi_count = first_line.matches(';').count();
            if tab_count > semi_count {
                return b'\t';
            }
        }
    }
    b';'
}

// 2. Parsing exact des pics selon VOTRE logique regex
fn parse_peak_list_native(peak_list_string: &str) -> Vec<(f64, f64)> {
    let mut peaks = Vec::new();
    for cap in crate::globals_vars::PEAK_LIST_JSON_PATTERN.captures_iter(peak_list_string) {
        let mz_str = cap[1].replace(",", ".");
        let int_str = cap[2].replace(",", ".");
        if let (Ok(mz), Ok(intensity)) = (mz_str.parse::<f64>(), int_str.parse::<f64>()) {
            peaks.push((mz, intensity)); // Utilisation de tuples pour optimiser la RAM
        }
    }
    peaks
}

// 3. La fonction principale qui remplace Pandas et csv_to_dict_processing
pub fn load_and_parse_csv(
    py: Python,
    csv_files: Vec<String>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<Spectrum>> {

    let total_files = csv_files.len();
    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total_files, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, ("Reading CSV files:",)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("csv_files",)); }

    let mut result_list = Vec::new();
    let mut processed_files = 0;

    for file_path in csv_files {
        let file_hash = generate_file_hash(&file_path);
        let filename = std::path::Path::new(&file_path)
            .file_name()
            .unwrap_or_default()
            .to_string_lossy()
            .into_owned();

        let separator = detect_separator(&file_path);

        let mut rdr = csv::ReaderBuilder::new()
            .delimiter(separator)
            .has_headers(true)
            .from_path(&file_path)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        let headers: Vec<String> = rdr.headers()
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?
            .iter()
            .map(|h| h.to_lowercase())
            .collect();

        for result in rdr.records() {
            let record = result.map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
            let mut spec = Spectrum::default();

            spec.metadata.insert("FILENAME".to_string(), filename.clone());
            spec.metadata.insert("FILEHASH".to_string(), file_hash.clone());

            for (i, field) in record.iter().enumerate() {
                if i >= headers.len() { continue; }
                let header = &headers[i];

                if header == "peaks" || header == "peaks_list" {
                    spec.peaks = parse_peak_list_native(field);
                    continue;
                }

                if let Some(mapped_key) = keys_dict.get(header) {
                    if keys_list.contains(mapped_key) {
                        spec.metadata.insert(mapped_key.clone(), field.to_string());
                    }
                }
            }

            for key in &keys_list {
                if !spec.metadata.contains_key(key) && key != "PEAKS_LIST" {
                    spec.metadata.insert(key.clone(), "".to_string());
                }
            }

            result_list.push(spec);
        }

        processed_files += 1;
        if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed_files,)); }

        py.allow_threads(|| { std::thread::sleep(std::time::Duration::from_millis(1)); });
    }

    Ok(result_list)
}