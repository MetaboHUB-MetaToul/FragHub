// src/convertors/mgf_to_dict.rs

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use std::collections::HashMap;

// 1. La structure pour passer les données entre les cœurs CPU sans bloquer Python
struct ParsedSpectrum {
    metadata: HashMap<String, String>,
    peaks: Vec<Vec<f64>>,
}

#[pyfunction]
#[pyo3(signature = (final_mgf, keys_dict, keys_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn mgf_to_dict_processing<'py>(
    py: Python<'py>,
    final_mgf: Vec<String>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyList>> {
    let total = final_mgf.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total, 0))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Parsing MGF spectrums:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let result_list = PyList::empty_bound(py);
    let mut processed = 0;

    // Découpage par paquets (chunks) comme dans votre version Python
    let chunk_size = 2000;

    for chunk in final_mgf.chunks(chunk_size) {

        // ====================================================================
        // ÉTAPE 1 : MULTITHREADING PUR RUST (Équivalent de ThreadPoolExecutor)
        // ====================================================================
        let parsed_chunk: Vec<ParsedSpectrum> = chunk.par_iter().filter_map(|spectrum| {
            // Attention : Assurez-vous d'avoir bien retiré le "?" dans globals_vars.rs
            // pour METADATA_PEAK_LIST_SPLIT_PATTERN_MGF comme discuté précédemment !
            if let Some(caps) = crate::globals_vars::METADATA_PEAK_LIST_SPLIT_PATTERN_MGF.captures(spectrum) {
                let metadata_str = caps.get(1).map_or("", |m| m.as_str());
                let peaks_str = caps.get(2).map_or("", |m| m.as_str());

                if !metadata_str.is_empty() && !peaks_str.is_empty() {
                    let mut metadata_dict: HashMap<String, String> = HashMap::new();

                    // Extraction des métadonnées
                    for m in crate::globals_vars::METADATA_PATTERN_MGF.captures_iter(metadata_str) {
                        let k_raw = m.get(1).unwrap().as_str();
                        let v_raw = m.get(2).unwrap().as_str();

                        let k = crate::globals_vars::METADATA_FIELDS_NAME_PATTERN.replace_all(k_raw, "").to_lowercase().trim().to_string();
                        let v = crate::globals_vars::METADATA_STRIP_VALUE_PATTERN.replace_all(v_raw, "").to_string();
                        metadata_dict.insert(k, v);
                    }

                    if !metadata_dict.is_empty() {
                        let mut peaks_array = Vec::new();

                        // Extraction des pics
                        for p in crate::globals_vars::PEAK_LIST_SPLIT_PATTERN.captures_iter(peaks_str) {
                            let mz = p.get(1).unwrap().as_str().replace(",", ".").parse::<f64>().unwrap_or(0.0);
                            let int = p.get(2).unwrap().as_str().replace(",", ".").parse::<f64>().unwrap_or(0.0);
                            peaks_array.push(vec![mz, int]);
                        }

                        // Si on a des métadonnées ET des pics, on valide le spectre
                        if !peaks_array.is_empty() {
                            return Some(ParsedSpectrum { metadata: metadata_dict, peaks: peaks_array });
                        }
                    }
                }
            }
            None // Équivalent de "if not metadata or not peak_list: return None"
        }).collect();

        // ====================================================================
        // ÉTAPE 2 : RETOUR À PYTHON (Mapping et création du dictionnaire)
        // ====================================================================
        for parsed in parsed_chunk {
            let final_dict = PyDict::new_bound(py);

            for (k, v) in parsed.metadata {
                if let Some(mapped) = keys_dict.get(&k) {
                    if keys_list.contains(mapped) {
                        final_dict.set_item(mapped, v)?;
                    }
                }
            }

            // Ajout de la liste de pics
            if let Some(mapped_peak) = keys_dict.get("peaks") {
                final_dict.set_item(mapped_peak, parsed.peaks)?;
            } else {
                final_dict.set_item("PEAKS_LIST", parsed.peaks)?;
            }

            // Complétion des clés manquantes
            for key in &keys_list {
                if !final_dict.contains(key)? { final_dict.set_item(key, "")?; }
            }

            result_list.append(final_dict)?;
        }

        // ====================================================================
        // ÉTAPE 3 : MISE À JOUR DE LA BARRE DE PROGRESSION VUE.JS
        // ====================================================================
        processed += chunk.len();
        if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
    }

    Ok(result_list)
}