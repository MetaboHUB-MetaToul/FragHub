import re

with open('scripts/fraghub_rust/src/complete_from_pubchem_datas.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyDict, PyList, PyAny};", "use pyo3::prelude::*;\nuse crate::spectrum::Spectrum;")

content = content.replace("#[pyfunction]\n#[pyo3(signature = (spectrum_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")

content = content.replace("pub fn complete_from_pubchem_datas<'py>(", "pub fn complete_from_pubchem_datas(")

content = content.replace("spectrum_list: &Bound<'py, PyList>,", "mut spectrum_list: Vec<Spectrum>,")
content = content.replace("-> PyResult<Bound<'py, PyList>> {", "-> PyResult<Vec<Spectrum>> {")

old_loop = """    // --- Step 3: Boucle de mise à jour ---
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

    Ok(spectrum_list.clone())"""

new_loop = """    // --- Step 3: Boucle de mise à jour ---
    for spec in spectrum_list.iter_mut() {
        let inchikey = spec.metadata.get("INCHIKEY").cloned().unwrap_or_default();

        if !inchikey.is_empty() && inchikey.to_lowercase() != "nan" {
            if let Some(pubchem_row) = pubchem_dict.get(&inchikey) {
                for col in columns_to_update {
                    if let Some(new_val) = pubchem_row.get(*col) {
                        if !new_val.trim().is_empty() && new_val.to_lowercase() != "nan" {
                            spec.metadata.insert(col.to_string(), new_val.clone());
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

    Ok(spectrum_list)"""

content = content.replace(old_loop, new_loop)

with open('scripts/fraghub_rust/src/complete_from_pubchem_datas.rs', 'w') as f:
    f.write(content)
