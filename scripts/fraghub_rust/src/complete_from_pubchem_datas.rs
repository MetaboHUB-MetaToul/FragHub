// src/complete_from_pubchem_datas.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};

#[pyfunction]
#[pyo3(signature = (spectrum_list_df, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn complete_from_pubchem_datas<'py>(
    py: Python<'py>,
    spectrum_list_df: Bound<'py, PyAny>, // On accepte le DataFrame Pandas
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyAny>> {

    // --- Step 1: Initialization ---
    if let Some(cb) = &prefix_callback { cb.call1(py, ("enriching data from PubChem (Rust):",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    // On sauvegarde l'ordre des colonnes du DataFrame original
    let original_columns = spectrum_list_df.getattr("columns")?;

    // On convertit le DataFrame en liste de dictionnaires pour Rust (équivalent de to_dict('records'))
    let dict_list_py = spectrum_list_df.call_method1("to_dict", ("records",))?;
    let spectrum_list = dict_list_py.downcast::<PyList>()?;

    let total_items = spectrum_list.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    // --- Step 2: Récupération de pubchem_datas depuis Rust Global State ---
    let state = crate::global_state::STATE.read().unwrap();
    let pubchem_dict = &state.pubchem_datas;

    let columns_to_update = ["INCHI", "SMILES", "FORMULA", "NAME", "EXACTMASS", "AVERAGEMASS"];
    let mut processed = 0;

    // --- Step 3: Boucle de mise à jour ---
    for item in spectrum_list.iter() {
        let row = item.downcast::<PyDict>()?;

        if let Ok(Some(inchikey_py)) = row.get_item("INCHIKEY") {
            let inchikey = inchikey_py.extract::<String>().unwrap_or_default();

            if !inchikey.is_empty() && inchikey.to_lowercase() != "nan" {
                if let Some(pubchem_row) = pubchem_dict.get(&inchikey) {
                    for col in columns_to_update {
                        if let Some(new_val) = pubchem_row.get(col) {
                            if !new_val.trim().is_empty() && new_val.to_lowercase() != "nan" {
                                row.set_item(col, new_val)?;
                            }
                        }
                    }
                }
            }
        }

        processed += 1;
        // Barre de progression (throttled)
        if processed % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }

    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    // --- Step 4: Reconstruction du DataFrame Pandas propre ---
    let pandas = py.import_bound("pandas")?;
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("columns", original_columns)?; // On maintient l'ordre strict des colonnes !

    let args = (spectrum_list,);
    let updated_df = pandas.call_method("DataFrame", args, Some(&kwargs))?;

    Ok(updated_df)
}