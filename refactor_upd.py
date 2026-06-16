import re

with open('scripts/fraghub_rust/src/update_checker.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyDict, PyList};", "use pyo3::prelude::*;\nuse crate::spectrum::Spectrum;")
content = content.replace("#[pyfunction]\n#[pyo3(signature = (spectrum_list, output_directory, ordered_columns, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")
content = content.replace("pub fn check_for_update_processing<'py>(", "pub fn check_for_update_processing(")
content = content.replace("spectrum_list: Bound<'py, PyList>,", "mut spectrum_list: Vec<Spectrum>,")
content = content.replace("-> PyResult<(Bound<'py, PyList>, bool, usize)> {", "-> PyResult<(Vec<Spectrum>, bool, usize)> {")

old_loop = """    for i in 0..total_items {
        let item = spectrum_list.get_item(i).unwrap();
        let dict = item.downcast::<PyDict>()?;

        let splash = if let Ok(Some(s)) = dict.get_item("SPLASH") {
            if let Ok(s_str) = s.str() { s_str.to_str().unwrap_or("").to_string() } else { String::new() }
        } else { String::new() };

        if !splash.is_empty() && splash_set.contains(&splash) {
            indices_to_delete.push(i); // Déjà vu -> on supprime
        } else {
            indices_to_keep.push(i); // Nouveau -> on garde
            if !splash.is_empty() {
                new_splashes.push(splash);
            }
        }

        processed += 1;
        if processed % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }"""

new_loop = """    for (i, spec) in spectrum_list.iter().enumerate() {
        let splash = spec.metadata.get("SPLASH").cloned().unwrap_or_default();

        if !splash.is_empty() && splash_set.contains(&splash) {
            indices_to_delete.push(i); // Déjà vu -> on supprime
        } else {
            indices_to_keep.push(i); // Nouveau -> on garde
            if !splash.is_empty() {
                new_splashes.push(splash);
            }
        }

        processed += 1;
        if processed % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }"""

content = content.replace(old_loop, new_loop)

old_write_loop = """        for &idx in &indices_to_delete {
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
            // Si le fichier JSON était corrompu, on recrée l'objet
            let mut new_obj = serde_json::Map::new();
            for s in new_splashes {
                new_obj.insert(s, serde_json::json!(true));
            }
            json_data["SPLASH_LIST"] = serde_json::Value::Object(new_obj);
        }

        let file = std::fs::File::create(&update_file_path).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
        serde_json::to_writer_pretty(file, &json_data).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
    }

    // 5. Générer la liste Python finale
    let final_list = PyList::empty_bound(py);
    for &idx in &indices_to_keep {
        final_list.append(spectrum_list.get_item(idx).unwrap())?;
    }"""

new_write_loop = """        for &idx in &indices_to_delete {
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

    // 5. Générer la liste finale
    let mut final_list = Vec::with_capacity(indices_to_keep.len());
    let mut current_idx = 0;
    for spec in spectrum_list.into_iter() {
        if indices_to_keep.contains(&current_idx) {
            final_list.push(spec);
        }
        current_idx += 1;
    }"""

content = content.replace(old_write_loop, new_write_loop)

with open('scripts/fraghub_rust/src/update_checker.rs', 'w') as f:
    f.write(content)
