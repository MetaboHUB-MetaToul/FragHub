use pyo3::prelude::*;
use crate::spectrum::Spectrum;

pub fn normalize_to_not_found_processing(
    py: Python,
    mut spectrum_list: Vec<Spectrum>,
) -> PyResult<Vec<Spectrum>> {
    for spec in spectrum_list.iter_mut() {
        for val in spec.metadata.values_mut() {
            if val.is_empty() {
                *val = "NOT FOUND".to_string();
            }
        }
    }
    Ok(spectrum_list)
}