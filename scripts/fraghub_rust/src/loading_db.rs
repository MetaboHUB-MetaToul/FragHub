use pyo3::prelude::*;
use pyo3::types::PyDict;
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;
use csv::ReaderBuilder;

// Les fonctions internes (pas besoin de pub)
fn read_csv_to_columns(filepath: &str, sep: u8) -> Result<HashMap<String, Vec<String>>, Box<dyn std::error::Error + Send + Sync>> {
    let mut rdr = ReaderBuilder::new()
        .delimiter(sep)
        .quote(b'"')
        .from_path(filepath)?;

    let headers: Vec<String> = rdr.headers()?.iter().map(|s| s.to_string()).collect();
    let mut columns: Vec<Vec<String>> = vec![Vec::new(); headers.len()];

    for result in rdr.records() {
        let record = result?;
        for (i, field) in record.iter().enumerate() {
            if i < columns.len() {
                columns[i].push(field.to_string());
            }
        }
    }

    let mut map = HashMap::new();
    for (header, column) in headers.into_iter().zip(columns.into_iter()) {
        map.insert(header, column);
    }
    Ok(map)
}

fn read_multiple_csvs(folder_path: &str, sep: u8, filter_str: &str) -> HashMap<String, Vec<String>> {
    let mut paths = Vec::new();
    if let Ok(entries) = fs::read_dir(folder_path) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() {
                if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                    if name.ends_with(".csv") && (filter_str.is_empty() || name.contains(filter_str)) {
                        paths.push(path.to_string_lossy().to_string());
                    }
                }
            }
        }
    }

    let results: Vec<_> = paths.par_iter().map(|p| {
        read_csv_to_columns(p, sep)
    }).collect();

    let mut merged: HashMap<String, Vec<String>> = HashMap::new();
    for res in results {
        if let Ok(map) = res {
            if merged.is_empty() {
                merged = map;
            } else {
                for (k, mut v) in map {
                    if let Some(existing) = merged.get_mut(&k) {
                        existing.append(&mut v);
                    } else {
                        merged.insert(k, v);
                    }
                }
            }
        }
    }
    merged
}

// Les fonctions Python (on ajoute pub)
#[pyfunction]
pub fn load_pubchem_datas(py: Python, folder_path: &str) -> PyResult<PyObject> {
    let map = read_multiple_csvs(folder_path, b';', "pubchem_rdkit_clean_part");
    let dict = PyDict::new_bound(py);
    for (k, v) in map {
        dict.set_item(k, v)?;
    }
    Ok(dict.into())
}

#[pyfunction]
pub fn load_ontologies_datas(py: Python, folder_path: &str) -> PyResult<PyObject> {
    let map = read_multiple_csvs(folder_path, b';', "ontologies_dict");
    let dict = PyDict::new_bound(py);
    for (k, v) in map {
        dict.set_item(k, v)?;
    }
    Ok(dict.into())
}

#[pyfunction]
pub fn load_adducts(py: Python, filepath: &str) -> PyResult<(PyObject, PyObject, PyObject, PyObject)> {
    let mut rdr = ReaderBuilder::new()
        .delimiter(b';')
        .from_path(filepath)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let mut adduct_dict_pos = HashMap::new();
    let mut adduct_massdiff_dict_pos = HashMap::new();
    let mut adduct_dict_neg = HashMap::new();
    let mut adduct_massdiff_dict_neg = HashMap::new();

    let headers = rdr.headers().map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?.clone();

    let mut idx_known = 0;
    let mut idx_default = 1;
    let mut idx_massdiff = 2;
    let mut idx_ionmode = 3;
    for (i, h) in headers.iter().enumerate() {
        match h {
            "known_adduct" => idx_known = i,
            "fraghub_default" => idx_default = i,
            "massdiff" => idx_massdiff = i,
            "ionmode" => idx_ionmode = i,
            _ => {}
        }
    }

    for result in rdr.records() {
        let record = result.map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let known = record.get(idx_known).unwrap_or("").to_string();
        let default = record.get(idx_default).unwrap_or("").to_string();
        let massdiff_str = record.get(idx_massdiff).unwrap_or("0.0");
        let massdiff: f64 = massdiff_str.parse().unwrap_or(0.0);
        let ionmode = record.get(idx_ionmode).unwrap_or("");

        if ionmode == "positive" {
            adduct_dict_pos.insert(known.clone(), default.clone());
            adduct_massdiff_dict_pos.insert(default.clone(), massdiff);
        } else if ionmode == "negative" {
            adduct_dict_neg.insert(known.clone(), default.clone());
            adduct_massdiff_dict_neg.insert(default.clone(), massdiff);
        }
    }

    let dict_pos = PyDict::new_bound(py);
    for (k, v) in adduct_dict_pos { dict_pos.set_item(k, v)?; }

    let mdict_pos = PyDict::new_bound(py);
    for (k, v) in adduct_massdiff_dict_pos { mdict_pos.set_item(k, v)?; }

    let dict_neg = PyDict::new_bound(py);
    for (k, v) in adduct_dict_neg { dict_neg.set_item(k, v)?; }

    let mdict_neg = PyDict::new_bound(py);
    for (k, v) in adduct_massdiff_dict_neg { mdict_neg.set_item(k, v)?; }

    Ok((dict_pos.into(), mdict_pos.into(), dict_neg.into(), mdict_neg.into()))
}

#[pyfunction]
pub fn load_keys(py: Python, filepath: &str) -> PyResult<PyObject> {
    let mut rdr = ReaderBuilder::new()
        .delimiter(b';')
        .from_path(filepath)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

    let mut keys_dict = HashMap::new();

    let headers = rdr.headers().map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?.clone();
    let mut idx_known = 0;
    let mut idx_default = 1;
    for (i, h) in headers.iter().enumerate() {
        match h {
            "known_synonym" => idx_known = i,
            "fraghub_default" => idx_default = i,
            _ => {}
        }
    }

    for result in rdr.records() {
        let record = result.map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
        let known = record.get(idx_known).unwrap_or("").to_string();
        let default = record.get(idx_default).unwrap_or("").to_uppercase();
        keys_dict.insert(known, default);
    }

    let dict = PyDict::new_bound(py);
    for (k, v) in keys_dict {
        dict.set_item(k, v)?;
    }
    Ok(dict.into())
}

#[pyfunction]
pub fn load_instrument_tree(py: Python, filepath: &str) -> PyResult<PyObject> {
    let content = fs::read_to_string(filepath)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
    let json_module = py.import_bound("json")?;
    let res = json_module.call_method1("loads", (content,))?;
    Ok(res.into())
}