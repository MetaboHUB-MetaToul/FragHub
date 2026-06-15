// src/ontologies_completion.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};

#[pyfunction]
#[pyo3(signature = (spectrum_list_df, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn ontologies_completion_processing<'py>(
    py: Python<'py>,
    spectrum_list_df: Bound<'py, PyAny>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyAny>> {

    // --- Step 1: Initialization ---
    if let Some(cb) = &prefix_callback { cb.call1(py, ("updating ontologies (Rust):",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    // On sauvegarde l'ordre des colonnes
    let original_columns = spectrum_list_df.getattr("columns")?;

    // On convertit le DataFrame en liste de dictionnaires
    let dict_list_py = spectrum_list_df.call_method1("to_dict", ("records",))?;
    let spectrum_list = dict_list_py.downcast::<PyList>()?;

    // Contrairement à votre Python qui simulait la progression avec le nombre de clés uniques,
    // on va faire une vraie progression fluide basée sur le nombre total de lignes.
    let total_items = spectrum_list.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    // --- Step 2: Récupération de ontologies_df depuis Python ---
    let globals = py.import_bound("scripts.globals_vars")?;
    let ontologies_df = globals.getattr("ontologies_df")?;

    // Transformation en dictionnaire ultra-rapide {INCHIKEY: {colonnes...}}
    let ont_dict_py = ontologies_df
        .call_method1("set_index", ("INCHIKEY",))?
        .call_method1("to_dict", ("index",))?;
    let ont_dict = ont_dict_py.downcast::<PyDict>()?;

    let columns_to_update = [
        "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS",
        "NPCLASS_PATHWAY", "NPCLASS_SUPERCLASS", "NPCLASS_CLASS"
    ];

    let mut processed = 0;

    // --- Step 3: Boucle de mise à jour (In-place) ---
    for item in spectrum_list.iter() {
        let row = item.downcast::<PyDict>()?;

        // Par défaut, on initialise tout à "NOT FOUND" comme dans votre code Python
        for col in columns_to_update {
            row.set_item(col, "NOT FOUND")?;
        }

        // Si on a un INCHIKEY valide, on cherche dans la base de données
        if let Ok(Some(inchikey_py)) = row.get_item("INCHIKEY") {
            let inchikey = inchikey_py.extract::<String>().unwrap_or_default();

            if !inchikey.is_empty() && inchikey.to_lowercase() != "nan" {
                if let Ok(Some(ont_row_py)) = ont_dict.get_item(&inchikey) {
                    if let Ok(ont_row) = ont_row_py.downcast::<PyDict>() {

                        // On a trouvé les données, on les injecte !
                        for col in columns_to_update {
                            if let Ok(Some(new_val_py)) = ont_row.get_item(col) {
                                let new_val = new_val_py.extract::<String>().unwrap_or_else(|_| new_val_py.to_string());
                                if !new_val.trim().is_empty() && new_val.to_lowercase() != "nan" {
                                    row.set_item(col, new_val)?;
                                }
                            }
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

    // --- Step 4: Reconstruction du DataFrame ---
    let pandas = py.import_bound("pandas")?;
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("columns", original_columns)?;

    let args = (spectrum_list,);
    let updated_df = pandas.call_method("DataFrame", args, Some(&kwargs))?;

    Ok(updated_df)
}