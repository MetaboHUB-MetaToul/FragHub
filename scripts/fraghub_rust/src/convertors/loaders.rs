// src/convertors/loaders.rs

use pyo3::prelude::*;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use sha2::{Sha256, Digest};
use regex::Regex;

/// Gets the size of a file in bytes, converts it to a string, and returns the SHA-256 hash.
#[pyfunction]
pub fn generate_file_hash(file_path: &str) -> String {
    if let Ok(metadata) = std::fs::metadata(file_path) {
        let size = metadata.len().to_string();
        let mut hasher = Sha256::new();
        hasher.update(size.as_bytes());
        format!("{:x}", hasher.finalize())
    } else {
        format!("Error: File not found at {}", file_path)
    }
}

#[pyfunction]
#[pyo3(signature = (msp_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_from_msp(
    py: Python,
    msp_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<String>> {
    let file_hash = generate_file_hash(msp_file_path);
    let path = Path::new(msp_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let file = File::open(msp_file_path)?;
    let mut reader = BufReader::new(&file);

    // Étape 1 : Compter le nombre de spectres
    let mut num_spectra = 0;
    let mut line = String::new();
    while reader.read_line(&mut line)? > 0 {
        if line.trim().is_empty() {
            num_spectra += 1;
        }
        line.clear();
    }

    // Étape 2 : Exécuter les callbacks d'initialisation
    if let Some(cb) = &total_items_callback { cb.call1(py, (num_spectra, 0))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, (format!("loading [{}]:", filename),))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    // Étape 3 à 6 : Lecture et parsing
    let file = File::open(msp_file_path)?;
    let mut reader = BufReader::new(file);
    let mut spectrum_list = Vec::new();
    let mut buffer = vec![format!("FILENAME: {}", filename)];
    let mut processed_spectra = 0;

    let re = Regex::new(r"(?i)FILENAME: .*\n").unwrap();
    let replacement = format!("FILENAME: {}\nFILEHASH: {}\n", filename, file_hash);

    line.clear();
    while reader.read_line(&mut line)? > 0 {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            if buffer.len() > 1 {
                let spectrum = buffer.join("\n") + "\n";
                let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
                spectrum_list.push(replaced.trim_end().to_string());
                buffer = vec![format!("FILENAME: {}", filename)];

                processed_spectra += 1;
                if let Some(cb) = &progress_callback { cb.call1(py, (processed_spectra,))?; }
            }
        } else {
            buffer.push(trimmed.to_string());
        }
        line.clear();
    }

    if buffer.len() > 1 {
        let spectrum = buffer.join("\n") + "\n";
        let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
        spectrum_list.push(replaced.trim_end().to_string());
    }

    Ok(spectrum_list)
}

#[pyfunction]
#[pyo3(signature = (mgf_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_from_mgf(
    py: Python,
    mgf_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<String>> {
    let file_hash = generate_file_hash(mgf_file_path);
    let path = Path::new(mgf_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    let file = File::open(mgf_file_path)?;
    let mut reader = BufReader::new(&file);

    let mut num_spectra = 0;
    let mut line = String::new();
    while reader.read_line(&mut line)? > 0 {
        if line.trim() == "END IONS" {
            num_spectra += 1;
        }
        line.clear();
    }

    if let Some(cb) = &total_items_callback { cb.call1(py, (num_spectra, 0))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, (format!("Loading [{}]:", filename),))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let file = File::open(mgf_file_path)?;
    let mut reader = BufReader::new(file);
    let mut spectrum_list = Vec::new();
    let mut buffer = vec![format!("FILENAME={}", filename)];
    let mut processed_items = 0;

    let re = Regex::new(r"(?i)FILENAME=.*\n").unwrap();
    let replacement = format!("FILENAME={}\nFILEHASH={}\n", filename, file_hash);

    line.clear();
    while reader.read_line(&mut line)? > 0 {
        let trimmed = line.trim();
        if trimmed == "END IONS" {
            if !buffer.is_empty() {
                let spectrum = buffer.join("\n") + "\n";
                let replaced = re.replace(&spectrum, replacement.as_str()).to_string();
                spectrum_list.push(replaced.trim_end().to_string());
                buffer = vec![format!("FILENAME={}", filename)];

                processed_items += 1;
                if let Some(cb) = &progress_callback { cb.call1(py, (processed_items,))?; }
            }
        } else {
            buffer.push(trimmed.to_string());
        }
        line.clear();
    }

    Ok(spectrum_list)
}

#[pyfunction]
#[pyo3(signature = (json_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_json(
    py: Python,
    json_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<PyObject>> {
    let file_hash = generate_file_hash(json_file_path);
    let path = Path::new(json_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    if let Some(cb) = &prefix_callback { cb.call1(py, (format!("loading [{}]:", filename),))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let file = File::open(json_file_path)?;
    let reader = BufReader::new(file);

    let v: serde_json::Value = serde_json::from_reader(reader).map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    let items = v.as_array().ok_or_else(|| pyo3::exceptions::PyValueError::new_err("Expected JSON array"))?;

    if let Some(cb) = &total_items_callback { cb.call1(py, (items.len(), 0))?; }

    let mut result = Vec::with_capacity(items.len());
    let mut processed = 0;
    let json_mod = py.import_bound("json")?;

    for item in items {
        let json_str = item.to_string();
        let py_dict = json_mod.call_method1("loads", (json_str,))?;
        py_dict.set_item("filename", &filename)?;
        py_dict.set_item("filehash", &file_hash)?;
        result.push(py_dict.into());

        processed += 1;
        if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
    }

    Ok(result)
}

#[pyfunction]
#[pyo3(signature = (json_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn load_spectrum_list_json_2(
    py: Python,
    json_file_path: &str,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<PyObject>> {
    let file_hash = generate_file_hash(json_file_path);
    let path = Path::new(json_file_path);
    let filename = path.file_name().unwrap_or_default().to_string_lossy().to_string();

    if let Some(cb) = &prefix_callback { cb.call1(py, (format!("loading [{}]:", filename),))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let file = File::open(json_file_path)?;
    let reader = BufReader::new(&file);
    let total_items = reader.lines().filter_map(Result::ok).filter(|l| !l.trim().is_empty()).count();

    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    let mut result = Vec::with_capacity(total_items);
    let mut processed = 0;
    let json_mod = py.import_bound("json")?;

    let file = File::open(json_file_path)?;
    let reader = BufReader::new(file);

    for line in reader.lines() {
        if let Ok(l) = line {
            if !l.trim().is_empty() {
                let py_dict = json_mod.call_method1("loads", (l.trim(),))?;
                py_dict.set_item("filename", &filename)?;
                py_dict.set_item("filehash", &file_hash)?;
                result.push(py_dict.into());

                processed += 1;
                if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
            }
        }
    }

    Ok(result)
}