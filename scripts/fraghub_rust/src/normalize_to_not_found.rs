// src/normalize_to_not_found.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};

#[pyfunction]
#[pyo3(signature = (spectrum_list_df))]
pub fn normalize_to_not_found_processing<'py>(
    py: Python<'py>,
    spectrum_list_df: Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {

    // On sauvegarde l'ordre des colonnes du DataFrame original
    let original_columns = spectrum_list_df.getattr("columns")?;

    // On convertit le DataFrame Pandas en liste de dictionnaires pour Rust
    let dict_list_py = spectrum_list_df.call_method1("to_dict", ("records",))?;
    let spectrum_list = dict_list_py.downcast::<PyList>()?;

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

    // Reconstruction du DataFrame Pandas
    let pandas = py.import_bound("pandas")?;
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("columns", original_columns)?;

    let args = (spectrum_list,);
    let updated_df = pandas.call_method("DataFrame", args, Some(&kwargs))?;

    Ok(updated_df)
}