// src/convertors/json_to_dict.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;
use rayon::prelude::*;
use std::collections::HashMap;
use std::time::Duration;


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
            // SAFETY: Les octets sont garantis être des chiffres/symboles ASCII valides
            let s_val = unsafe { std::str::from_utf8_unchecked(&bytes[s..i]) };
            if let Ok(num) = s_val.parse::<f64>() { numbers.push(num); }
            start = None;
        }
    }
    if let Some(s) = start {
        let s_val = unsafe { std::str::from_utf8_unchecked(&bytes[s..]) };
        if let Ok(num) = s_val.parse::<f64>() { numbers.push(num); }
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

pub fn json_to_dict_processing(
    py: Python,
    mut rust_strings: Vec<String>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<Spectrum>> {



    let total = rust_strings.len();
    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, ("Parsing JSON spectrums:",)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let mut result_list = Vec::new();

    let mut processed = 0;
    let chunk_size = 3000;

    // --- BOUCLIER RAM 2 : Extraction rapide par la fin (O(1) déplacement) ---
    while !rust_strings.is_empty() {
        let end = rust_strings.len();
        let start = if end > chunk_size { end - chunk_size } else { 0 };
        let chunk: Vec<String> = rust_strings.drain(start..end).collect();
        let current_chunk_len = chunk.len();

        let parsed_chunk: Vec<ParsedJsonSpectrum> = py.allow_threads(|| {
            chunk.into_par_iter().filter_map(|json_str| {
                let v: serde_json::Value = serde_json::from_str(&json_str).ok()?;
                let mut metadata = HashMap::with_capacity(32);
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
                                    if name_lower == "molecular formula" ||
                                       name_lower == "smiles" ||
                                       name_lower == "inchi" ||
                                       name_lower == "inchikey" {
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
                                if name_lower == "instrument" ||
                                   name_lower == "instrument type" ||
                                   name_lower == "ms level" ||
                                   name_lower == "ionization" ||
                                   name_lower == "retention time" ||
                                   name_lower == "ionization mode" ||
                                   name_lower == "precursor type" ||
                                   name_lower == "collision energy" ||
                                   name_lower == "precursor m/z" {
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
                            let k_str = k.as_str();
                            if k_str != "spectrum" && k_str != "peaks_json" && k_str != "peaks" {
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
            let mut spec = Spectrum::default();

            for (k, val) in parsed.metadata {
                if let Some(mapped) = keys_dict.get(&k) {
                    if keys_list.contains(mapped) {
                        spec.metadata.insert(mapped.clone(), val);
                    }
                }
            }

            spec.peaks = parsed.peaks;

            for key in &keys_list {
                if !spec.metadata.contains_key(key) && key != "PEAKS_LIST" {
                    spec.metadata.insert(key.clone(), "".to_string());
                }
            }

            result_list.push(spec);
        }

        processed += current_chunk_len;
        if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed,)); }

        py.allow_threads(|| { std::thread::sleep(Duration::from_millis(1)); });
    }

    Ok(result_list)
}
