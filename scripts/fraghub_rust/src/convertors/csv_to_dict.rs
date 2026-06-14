// src/convertors/csv_to_dict.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use regex::Regex;
use std::collections::HashMap;

fn parse_peak_list(py: Python, peak_list_string: &str) -> PyResult<PyObject> {
    let mut peaks = Vec::new();
    for cap in crate::globals_vars::PEAK_LIST_JSON_PATTERN.captures_iter(peak_list_string) {
        let mz_str = cap[1].replace(",", ".");
        let int_str = cap[2].replace(",", ".");
        if let (Ok(mz), Ok(intensity)) = (mz_str.parse::<f64>(), int_str.parse::<f64>()) {
            peaks.push(vec![mz, intensity]);
        }
    }
    Ok(PyList::new_bound(py, peaks).into())
}

#[pyfunction]
#[pyo3(signature = (final_csv, keys_dict, keys_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn csv_to_dict_processing<'py>(
    py: Python<'py>,
    final_csv: Bound<'py, PyList>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyList>> {
    let total = final_csv.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total, 0))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Parsing CSV spectrums:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    let mut processed = 0;
    let result_list = PyList::empty_bound(py);

    for i in 0..total {
        let row = final_csv.get_item(i)?.downcast_into::<PyDict>()?;

        // 1. Process Peaks
        if let Ok(Some(peaks_val)) = row.get_item("peaks") {
            if let Ok(s) = peaks_val.extract::<String>() {
                row.set_item("peaks", parse_peak_list(py, &s)?)?;
            }
        } else if let Ok(Some(peaks_list_val)) = row.get_item("peaks_list") {
            if let Ok(s) = peaks_list_val.extract::<String>() {
                row.set_item("peaks", parse_peak_list(py, &s)?)?;
            }
        }

        // 2. Convert Keys
        let new_dict = PyDict::new_bound(py);
        for (k, v) in row.iter() {
            if let Ok(k_str) = k.extract::<String>() {
                let lower_k = k_str.to_lowercase();
                if let Some(mapped_key) = keys_dict.get(&lower_k) {
                    if keys_list.contains(mapped_key) {
                        new_dict.set_item(mapped_key, v)?;
                    }
                }
            }
        }
        for key in &keys_list {
            if !new_dict.contains(key)? {
                new_dict.set_item(key, "")?;
            }
        }

        result_list.append(new_dict)?;

        processed += 1;
        if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
    }

    Ok(result_list)
}