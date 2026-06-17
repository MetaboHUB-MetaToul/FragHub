// src/convertors/msp_to_dict.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;
use rayon::prelude::*;
use std::collections::HashMap;


struct ParsedSpectrum {
    metadata: HashMap<String, String>,
    peaks: Vec<(f64, f64)>, // <-- TUPLES : Fini la fragmentation mémoire !
}

pub fn msp_to_dict_processing(
    py: Python,
    rust_strings: Vec<String>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<Spectrum>> {



    let total = rust_strings.len();
    if let Some(cb) = &total_items_callback { let _ = cb.call1(py, (total, 0)); }
    if let Some(cb) = &prefix_callback { let _ = cb.call1(py, ("Parsing MSP spectra:",)); }
    if let Some(cb) = &item_type_callback { let _ = cb.call1(py, ("spectra",)); }

    let mut result_list = Vec::new();
    let mut processed = 0;
    let chunk_size = 2000;

    for chunk in rust_strings.chunks(chunk_size) {

        let parsed_chunk: Vec<ParsedSpectrum> = py.allow_threads(|| {
            chunk.par_iter().filter_map(|spectrum| {
                if let Some(caps) = crate::globals_vars::METADATA_PEAK_LIST_SPLIT_PATTERN_MSP.captures(spectrum) {
                    let metadata_str = caps.get(1).map_or("", |m| m.as_str());
                    let peaks_str = caps.get(2).map_or("", |m| m.as_str());

                    if !metadata_str.is_empty() && !peaks_str.is_empty() {
                        let mut metadata_matches = Vec::new();
                        for m in crate::globals_vars::METADATA_PATTERN_MSP.captures_iter(metadata_str) {
                            metadata_matches.push((m.get(1).unwrap().as_str().to_string(), m.get(2).unwrap().as_str().to_string()));
                        }

                        let mut new_matches = Vec::new();
                        let mut valid_comments = true;
                        for (k, v) in metadata_matches {
                            if crate::globals_vars::COMMENT_PATTERN.is_match(&k) {
                                new_matches.push((k.clone(), v.clone()));
                                if v.contains("=") {
                                    let mut found_sub = false;
                                    for sub_m in crate::globals_vars::SUB_FIELDS_PATTERN.captures_iter(&v) {
                                        let mut g_k = String::new();
                                        let mut g_v = String::new();
                                        let mut count = 0;
                                        for i in 1..sub_m.len() {
                                            if let Some(grp) = sub_m.get(i) {
                                                if !grp.as_str().is_empty() {
                                                    if count == 0 { g_k = grp.as_str().to_string(); count += 1; }
                                                    else if count == 1 { g_v = grp.as_str().to_string(); count += 1; break; }
                                                }
                                            }
                                        }
                                        if count == 2 {
                                            new_matches.push((g_k, g_v));
                                            found_sub = true;
                                        }
                                    }
                                    if !found_sub { valid_comments = false; break; }
                                }
                            } else { new_matches.push((k, v)); }
                        }

                        if valid_comments && !new_matches.is_empty() {
                            let mut metadata_dict: HashMap<String, String> = HashMap::new();
                            for (k_raw, v_raw) in new_matches.into_iter().filter(|(k, _)| !crate::globals_vars::COMPUTED_PATTERN.is_match(k)) {
                                let k = crate::globals_vars::METADATA_FIELDS_NAME_PATTERN.replace_all(&k_raw, "").to_lowercase().trim().to_string();
                                let v = crate::globals_vars::METADATA_STRIP_VALUE_PATTERN.replace_all(&v_raw, "").to_string();
                                metadata_dict.insert(k, v);
                            }

                            let mut peaks_array = Vec::new();
                            for p in crate::globals_vars::PEAK_LIST_SPLIT_PATTERN.captures_iter(peaks_str) {
                                let mz = p.get(1).unwrap().as_str().replace(",", ".").parse::<f64>().unwrap_or(0.0);
                                let int = p.get(2).unwrap().as_str().replace(",", ".").parse::<f64>().unwrap_or(0.0);
                                peaks_array.push((mz, int)); // ✅ TUPLE AU LIEU D'UN VEC
                            }

                            if !peaks_array.is_empty() {
                                return Some(ParsedSpectrum { metadata: metadata_dict, peaks: peaks_array });
                            }
                        }
                    }
                }
                None
            }).collect()
        });

        for parsed in parsed_chunk {
            let mut spec = Spectrum::default();
            for (k, v) in parsed.metadata {
                if let Some(mapped) = keys_dict.get(&k) {
                    if keys_list.contains(mapped) {
                        spec.metadata.insert(mapped.clone(), v);
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

        processed += chunk.len();
        if let Some(cb) = &progress_callback { let _ = cb.call1(py, (processed,)); }
        py.allow_threads(|| { std::thread::sleep(std::time::Duration::from_millis(1)); });
    }

    Ok(result_list)
}