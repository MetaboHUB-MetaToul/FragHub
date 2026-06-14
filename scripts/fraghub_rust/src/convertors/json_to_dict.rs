// src/convertors/json_to_dict.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use regex::Regex;
use std::collections::HashMap;

fn parse_json_peak_list(py: Python, peak_list_string: &str) -> PyResult<PyObject> {
    let mut peaks = Vec::new();
    for cap in crate::globals_vars::PEAK_LIST_JSON_PATTERN.captures_iter(peak_list_string) {
        let mz = cap[1].replace(",", ".").parse::<f64>().unwrap_or(0.0);
        let int = cap[2].replace(",", ".").parse::<f64>().unwrap_or(0.0);
        peaks.push(vec![mz, int]);
    }
    Ok(PyList::new_bound(py, peaks).into())
}

fn parsing_mona_json<'py>(py: Python<'py>, json_dict: &Bound<'py, PyDict>) -> PyResult<Bound<'py, PyDict>> {
    let dict_final = PyDict::new_bound(py);

    // Compound name
    if let Ok(Some(compound)) = json_dict.get_item("compound") {
        if let Ok(comp_list) = compound.downcast::<PyList>() {
            if comp_list.len() > 0 {
                if let Ok(comp_0) = comp_list.get_item(0)?.downcast::<PyDict>() {
                    if let Ok(Some(names)) = comp_0.get_item("names") {
                        if let Ok(names_list) = names.downcast::<PyList>() {
                            if names_list.len() > 0 {
                                if let Ok(names_0) = names_list.get_item(0)?.downcast::<PyDict>() {
                                    if let Ok(Some(name_val)) = names_0.get_item("name") {
                                        dict_final.set_item("compound_name", name_val)?;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if !dict_final.contains("compound_name")? { dict_final.set_item("compound_name", "")?; }

    // Compound MetaData (smiles, inchi...)
    if let Ok(Some(compound)) = json_dict.get_item("compound") {
        if let Ok(comp_list) = compound.downcast::<PyList>() {
            if comp_list.len() > 0 {
                if let Ok(comp_0) = comp_list.get_item(0)?.downcast::<PyDict>() {
                    if let Ok(Some(meta)) = comp_0.get_item("metaData") {
                        if let Ok(meta_list) = meta.downcast::<PyList>() {
                            for i in 0..meta_list.len() {
                                if let Ok(item) = meta_list.get_item(i)?.downcast::<PyDict>() {
                                    if let (Ok(Some(name)), Ok(Some(computed))) = (item.get_item("name"), item.get_item("computed")) {
                                        let name_str = name.extract::<String>().unwrap_or_default().to_lowercase();
                                        let is_computed = computed.extract::<bool>().unwrap_or(false);
                                        if !is_computed && ["molecular formula", "smiles", "inchi", "inchikey"].contains(&name_str.as_str()) {
                                            if let Ok(Some(val)) = item.get_item("value") { dict_final.set_item(name_str, val)?; }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ID, global MetaData, filename...
    if let Ok(Some(id_val)) = json_dict.get_item("id") { dict_final.set_item("spectrum_id", id_val)?; }
    if let Ok(Some(f_val)) = json_dict.get_item("filename") { dict_final.set_item("filename", f_val)?; }

    if let Ok(Some(meta)) = json_dict.get_item("metaData") {
        if let Ok(meta_list) = meta.downcast::<PyList>() {
            for i in 0..meta_list.len() {
                if let Ok(item) = meta_list.get_item(i)?.downcast::<PyDict>() {
                    if let Ok(Some(name)) = item.get_item("name") {
                        let name_str = name.extract::<String>().unwrap_or_default().to_lowercase();
                        if ["instrument", "instrument type", "ms level", "ionization", "retention time", "ionization mode", "precursor type", "collision energy", "precursor m/z"].contains(&name_str.as_str()) {
                            if let Ok(Some(val)) = item.get_item("value") { dict_final.set_item(name_str, val)?; }
                        }
                    }
                }
            }
        }
    }

    // Spectrum (peaks)
    if let Ok(Some(spec_val)) = json_dict.get_item("spectrum") {
        if let Ok(spec_str) = spec_val.extract::<String>() {
            if let Ok(peaks) = parse_json_peak_list(py, &spec_str) { dict_final.set_item("peaks", peaks)?; }
        }
    }

    // Predicted
    dict_final.set_item("predicted", "false")?;
    if let Ok(Some(tags)) = json_dict.get_item("tags") {
        if let Ok(tags_list) = tags.downcast::<PyList>() {
            for i in 0..tags_list.len() {
                if let Ok(tag_dict) = tags_list.get_item(i)?.downcast::<PyDict>() {
                    if let Ok(Some(text)) = tag_dict.get_item("text") {
                        if text.extract::<String>().unwrap_or_default() == "In-Silico" {
                            dict_final.set_item("predicted", "true")?;
                            break;
                        }
                    }
                }
            }
        }
    }

    Ok(dict_final)
}

fn convert_dict_keys<'py>(py: Python<'py>, dict: &Bound<'py, PyDict>, keys_dict: &HashMap<String, String>, keys_list: &Vec<String>) -> PyResult<Bound<'py, PyDict>> {
    let new_dict = PyDict::new_bound(py);
    for (k, v) in dict.iter() {
        if let Ok(k_str) = k.extract::<String>() {
            let lower_k = k_str.to_lowercase();
            if let Some(mapped_key) = keys_dict.get(&lower_k) {
                if keys_list.contains(mapped_key) {
                    new_dict.set_item(mapped_key, v)?;
                }
            }
        }
    }
    for key in keys_list {
        if !new_dict.contains(key)? { new_dict.set_item(key, "")?; }
    }
    Ok(new_dict)
}

#[pyfunction]
#[pyo3(signature = (final_json, keys_dict, keys_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn json_to_dict_processing<'py>(
    py: Python<'py>,
    final_json: Bound<'py, PyList>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyList>> {
    let total = final_json.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total, 0))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Parsing JSON spectrums:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let mut processed = 0;
    let result_list = PyList::empty_bound(py);

    let keys_to_check = vec!["compound", "id", "metaData", "spectrum", "filename"];
    let peak_list_keys = vec!["spectrum", "peaks_json", "peaks"];

    for i in 0..total {
        if let Ok(json_dict) = final_json.get_item(i)?.downcast_into::<PyDict>() {
            let has_all_keys = keys_to_check.iter().all(|&k| json_dict.contains(k).unwrap_or(false));

            if has_all_keys {
                if let Ok(parsed_mona) = parsing_mona_json(py, &json_dict) {
                    let final_dict = convert_dict_keys(py, &parsed_mona, &keys_dict, &keys_list)?;
                    result_list.append(final_dict)?;
                }
            } else {
                let mut matched = false;
                for key in &peak_list_keys {
                    if json_dict.contains(key).unwrap_or(false) {
                        if let Ok(Some(val)) = json_dict.get_item(key) {
                            if let Ok(val_str) = val.extract::<String>() {
                                if let Ok(peaks) = parse_json_peak_list(py, &val_str) {
                                    json_dict.set_item(key, peaks)?;
                                    let final_dict = convert_dict_keys(py, &json_dict, &keys_dict, &keys_list)?;
                                    result_list.append(final_dict)?;
                                    matched = true;
                                    break;
                                }
                            }
                        }
                    }
                }
                if !matched { /* Le Python ne faisait rien, donc on filtre cet item */ }
            }
        }
        processed += 1;
        if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
    }

    Ok(result_list)
}