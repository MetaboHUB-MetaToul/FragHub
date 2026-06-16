// src/convertors/parsing_to_dict.rs
use pyo3::prelude::*;
use std::collections::HashMap;

use crate::convertors::loaders::{load_spectrum_list_json, load_spectrum_list_json_2, load_spectrum_list_from_msp, load_spectrum_list_from_mgf};
use crate::convertors::json_to_dict::json_to_dict_processing;
use crate::convertors::msp_to_dict::msp_to_dict_processing;
use crate::convertors::mgf_to_dict::mgf_to_dict_processing;
use crate::convertors::csv_to_dict::load_and_parse_csv;
use crate::spectrum::Spectrum;

pub fn parsing_to_dict_processing(
    py: Python,
    input_paths: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
    step_callback: Option<PyObject>,
) -> PyResult<(Vec<Spectrum>, Vec<Spectrum>, Vec<Spectrum>, Vec<Spectrum>)> {

    let (keys_dict, keys_list) = {
        let state = crate::global_state::STATE.read().unwrap();
        (state.keys_dict.clone(), state.keys_list.clone())
    };

    let mut final_json = Vec::new();
    let mut final_msp = Vec::new();
    let mut final_mgf = Vec::new();

    let mut json_files = Vec::new();
    let mut msp_files = Vec::new();
    let mut mgf_files = Vec::new();
    let mut csv_files = Vec::new();

    // Tri des fichiers par extension
    for path in input_paths {
        if path.ends_with(".json") { json_files.push(path); }
        else if path.ends_with(".msp") { msp_files.push(path); }
        else if path.ends_with(".mgf") { mgf_files.push(path); }
        else if path.ends_with(".csv") { csv_files.push(path); }
    }

    // ======================================================
    // JSON PROCESSING
    // ======================================================
    if !json_files.is_empty() {
        py.allow_threads(|| { std::thread::sleep(std::time::Duration::from_millis(10)); });
        if let Some(cb) = &step_callback { let _ = cb.call1(py, ("-- PARSING JSON TO DICT --",)); }

        for file in json_files {
            let raw_tunnel = match load_spectrum_list_json(py, &file, progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone()) {
                Ok(t) => t,
                Err(_) => load_spectrum_list_json_2(py, &file, progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone())?,
            };

            let raw_obj = raw_tunnel.into_py(py).into_bound(py);
            let dict_list = json_to_dict_processing(py, &raw_obj, keys_dict.clone(), keys_list.clone(), progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone())?;

            final_json.extend(dict_list);
        }
    }

    // ======================================================
    // MSP PROCESSING
    // ======================================================
    if !msp_files.is_empty() {
        py.allow_threads(|| { std::thread::sleep(std::time::Duration::from_millis(10)); });
        if let Some(cb) = &step_callback { let _ = cb.call1(py, ("-- PARSING MSP TO DICT --",)); }

        for file in msp_files {
            let raw_tunnel = load_spectrum_list_from_msp(py, &file, progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone())?;
            let raw_obj = raw_tunnel.into_py(py).into_bound(py);
            let dict_list = msp_to_dict_processing(py, &raw_obj, keys_dict.clone(), keys_list.clone(), progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone())?;

            final_msp.extend(dict_list);
        }
    }

    // ======================================================
    // MGF PROCESSING
    // ======================================================
    if !mgf_files.is_empty() {
        py.allow_threads(|| { std::thread::sleep(std::time::Duration::from_millis(10)); });
        if let Some(cb) = &step_callback { let _ = cb.call1(py, ("-- PARSING MGF TO DICT --",)); }

        let mut mgf_spectra = Vec::new();
        for file in mgf_files {
            let spectra = load_spectrum_list_from_mgf(py, &file, progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone())?;
            mgf_spectra.extend(spectra);
        }
        let dict_list = mgf_to_dict_processing(py, mgf_spectra, keys_dict.clone(), keys_list.clone(), progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone())?;

        final_mgf.extend(dict_list);
    }

    // ======================================================
    // CSV PROCESSING
    // ======================================================
    let mut final_csv = Vec::new();
    if !csv_files.is_empty() {
        py.allow_threads(|| { std::thread::sleep(std::time::Duration::from_millis(10)); });
        if let Some(cb) = &step_callback { let _ = cb.call1(py, ("-- PARSING CSV TO DICT --",)); }

        final_csv = load_and_parse_csv(py, csv_files, keys_dict, keys_list, progress_callback, total_items_callback, prefix_callback, item_type_callback)?;
    }

    Ok((final_msp, final_csv, final_json, final_mgf))
}
