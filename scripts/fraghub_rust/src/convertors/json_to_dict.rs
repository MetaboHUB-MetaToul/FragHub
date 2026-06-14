// src/convertors/json_to_dict.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyAny};
use rayon::prelude::*;
use std::collections::{HashMap, HashSet};
use std::time::Duration;

use super::loaders::RawJsonSpectra;

struct ParsedJsonSpectrum {
    metadata: HashMap<String, String>,
    peaks: Vec<(f64, f64)>,
}

fn parse_json_peak_list_rust(peak_list_string: &str) -> Vec<(f64, f64)> {
    let bytes = peak_list_string.as_bytes();
    let mut numbers = Vec::with_capacity(1024);
    let mut start = None;

    for (i, &b) in bytes.iter().enumerate() {
        let is_num_char = b.is_ascii_digit() || b == b'.' || b == b'-' || b == b'e' || b == b'E' || b == b'+';
        if is_num_char {
            if start.is_none() { start = Some(i); }
        } else if let Some(s) = start {
            if let Ok(s_val) = std::str::from_utf8(&bytes[s..i]) {
                if let Ok(num) = s_val.parse::<f64>() { numbers.push(num); }
            }
            start = None;
        }
    }
    if let Some(s) = start {
        if let Ok(s_val) = std::str::from_utf8(&bytes[s..]) {
            if let Ok(num) = s_val.parse::<f64>() { numbers.push(num); }
        }
    }

    let mut peaks = Vec::with_capacity(numbers.len() / 2);
    for chunk in numbers.chunks_exact(2) {
        peaks.push((chunk[0], chunk[1]));
    }
    peaks
}

fn parse_json_peak_array(val: &serde_json::Value) -> Vec<(f64, f64)> {
    let mut peaks = Vec::new();
    if let Some(arr) = val.as_array() {
        peaks.reserve(arr.len());
        for item in arr {
            if let Some(pair) = item.as_array() {
                if pair.len() >= 2 {
                    let mz = pair[0].as_f64().unwrap_or(0.0);
                    let int = pair[1].as_f64().unwrap_or(0.0);
                    peaks.push((mz, int));
                }
            }
        }
    }
    peaks
}

#[pyfunction]
#[pyo3(signature = (final_json_obj, keys_dict, keys_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn json_to_dict_processing<'py>(
    py: Python<'py>,
    final_json_obj: &Bound<'py, PyAny>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyList>> {

    let mut rust_strings: Vec<String> = Vec::new();

    if let Ok(mut raw) = final_json_obj.extract::<PyRefMut<'_, RawJsonSpectra>>() {
        rust_strings = std::mem::take(&mut raw.data);
    }
    else if let Ok(py_list) = final_json_obj.downcast::<PyList>() {
        for item in py_list {
            if let Ok(s) = item.extract::<String>() { rust_strings.push(s); }
        }
    }

    let total = rust_strings.len();
    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, ("Parsing JSON spectrums:",)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let result_list = PyList::empty_bound(py);
    let keys_set: HashSet<&str> = keys_list.iter().map(|s| s.as_str()).collect();

    // --- BOUCLIER RAM 1 : Mise en cache des 60 millions de clés ---
    let mut interned_keys: HashMap<String, Bound<'py, PyString>> = HashMap::new();
    for mapped in keys_dict.values() {
        if keys_set.contains(mapped.as_str()) {
            interned_keys.insert(mapped.clone(), PyString::intern_bound(py, mapped));
        }
    }
    let peaks_list_key = PyString::intern_bound(py, "PEAKS_LIST");

    let mut interned_keys_list = Vec::new();
    for key in &keys_list {
        interned_keys_list.push(PyString::intern_bound(py, key));
    }

    let mut processed = 0;
    let chunk_size = 2000;

    // --- BOUCLIER RAM 2 : Destruction des chaînes au vol ---
    rust_strings.reverse(); // On inverse pour utiliser pop() en 0 allocation

    while !rust_strings.is_empty() {
        let mut chunk = Vec::with_capacity(chunk_size);
        for _ in 0..chunk_size {
            if let Some(s) = rust_strings.pop() { chunk.push(s); }
            else { break; }
        }
        let current_chunk_len = chunk.len();

        let parsed_chunk: Vec<ParsedJsonSpectrum> = py.allow_threads(|| {
            // into_par_iter() détruit et libère la RAM à chaque ligne lue !
            chunk.into_par_iter().filter_map(|json_str| {
                let v: serde_json::Value = serde_json::from_str(&json_str).ok()?;
                let mut metadata = HashMap::new();
                let mut peaks = Vec::new();

                let is_mona = v.get("compound").is_some() && v.get("id").is_some() && v.get("metaData").is_some() && v.get("spectrum").is_some() && v.get("filename").is_some();

                if let Some(fh) = v.get("filehash").and_then(|h| h.as_str()) { metadata.insert("filehash".to_string(), fh.to_string()); }
                if let Some(fnm) = v.get("filename").and_then(|f| f.as_str()) { metadata.insert("filename".to_string(), fnm.to_string()); }

                if is_mona {
                    if let Some(comp_name) = v["compound"].get(0).and_then(|c| c["names"].get(0)).and_then(|n| n["name"].as_str()) {
                        metadata.insert("compound_name".to_string(), comp_name.to_string());
                    } else {
                        metadata.insert("compound_name".to_string(), "".to_string());
                    }

                    if let Some(meta) = v["compound"].get(0).and_then(|c| c["metaData"].as_array()) {
                        for item in meta {
                            if !item["computed"].as_bool().unwrap_or(false) {
                                if let Some(name) = item["name"].as_str() {
                                    let name_lower = name.to_lowercase();
                                    if ["molecular formula", "smiles", "inchi", "inchikey"].contains(&name_lower.as_str()) {
                                        if let Some(val) = item["value"].as_str() {
                                            metadata.insert(name_lower, val.to_string());
                                        }
                                    }
                                }
                            }
                        }
                    }

                    if let Some(id) = v["id"].as_str() { metadata.insert("spectrum_id".to_string(), id.to_string()); }

                    if let Some(meta) = v["metaData"].as_array() {
                        for item in meta {
                            if let Some(name) = item["name"].as_str() {
                                let name_lower = name.to_lowercase();
                                if ["instrument", "instrument type", "ms level", "ionization", "retention time", "ionization mode", "precursor type", "collision energy", "precursor m/z"].contains(&name_lower.as_str()) {
                                    if let Some(val) = item["value"].as_str() {
                                        metadata.insert(name_lower, val.to_string());
                                    } else if let Some(val) = item["value"].as_f64() {
                                        metadata.insert(name_lower, val.to_string());
                                    }
                                }
                            }
                        }
                    }

                    metadata.insert("predicted".to_string(), "false".to_string());
                    if let Some(tags) = v["tags"].as_array() {
                        for tag in tags {
                            if tag["text"].as_str() == Some("In-Silico") {
                                metadata.insert("predicted".to_string(), "true".to_string());
                                break;
                            }
                        }
                    }

                    if let Some(spec) = v["spectrum"].as_str() {
                        peaks = parse_json_peak_list_rust(spec);
                    }
                } else {
                    let mut matched = false;
                    for pk in ["spectrum", "peaks_json", "peaks"] {
                        if let Some(pval) = v.get(pk) {
                            if let Some(pstr) = pval.as_str() {
                                peaks = parse_json_peak_list_rust(pstr);
                            } else {
                                peaks = parse_json_peak_array(pval);
                            }
                            matched = true;
                            break;
                        }
                    }
                    if !matched { return None; }

                    if let Some(obj) = v.as_object() {
                        for (k, val) in obj {
                            if !["spectrum", "peaks_json", "peaks"].contains(&k.as_str()) {
                                if let Some(s) = val.as_str() {
                                    metadata.insert(k.to_lowercase(), s.to_string());
                                } else if val.is_number() || val.is_boolean() {
                                    metadata.insert(k.to_lowercase(), val.to_string());
                                }
                            }
                        }
                    }
                }

                Some(ParsedJsonSpectrum { metadata, peaks })
            }).collect()
        });

        for parsed in parsed_chunk {
            let final_dict = PyDict::new_bound(py);

            for (k, val) in parsed.metadata {
                if let Some(mapped) = keys_dict.get(&k) {
                    if let Some(interned_k) = interned_keys.get(mapped) {
                        let _ = final_dict.set_item(interned_k, val);
                    }
                }
            }

            if let Some(mapped_peak) = keys_dict.get("peaks") {
                if let Some(interned_k) = interned_keys.get(mapped_peak) {
                    let _ = final_dict.set_item(interned_k, parsed.peaks);
                } else {
                    let _ = final_dict.set_item(mapped_peak, parsed.peaks);
                }
            } else {
                let _ = final_dict.set_item(&peaks_list_key, parsed.peaks);
            }

            for interned_key in &interned_keys_list {
                if !final_dict.contains(interned_key).unwrap_or(false) {
                    let _ = final_dict.set_item(interned_key, "");
                }
            }

            let _ = result_list.append(final_dict);
        }

        processed += current_chunk_len;
        if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed,)); }

        py.allow_threads(|| { std::thread::sleep(Duration::from_millis(1)); });
    }

    Ok(result_list)
}