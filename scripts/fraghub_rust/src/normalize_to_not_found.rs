// src/normalize_to_not_found.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};

#[pyfunction]
#[pyo3(signature = (spectrum_list))]
pub fn normalize_to_not_found_processing<'py>(
    py: Python<'py>,
    spectrum_list: &Bound<'py, PyList>,
) -> PyResult<Bound<'py, PyList>> {

    // On parcourt chaque spectre
    for item in spectrum_list.iter() {
        if let Ok(dict) = item.downcast::<PyDict>() {

            // On collecte les clés vides en amont (sécurité mémoire PyO3)
            let mut keys_to_update = Vec::new();

            for (k, v) in dict.iter() {
                if let Ok(val_str) = v.extract::<String>() {
                    if val_str.is_empty() {
                        if let Ok(key_str) = k.extract::<String>() {
                            keys_to_update.push(key_str);
                        }
                    }
                }
            }

            // On applique le remplacement ("In-place", pas d'allocation de nouvelle liste)
            for k in keys_to_update {
                dict.set_item(k, "NOT FOUND")?;
            }
        }
    }

    Ok(spectrum_list.clone())
}