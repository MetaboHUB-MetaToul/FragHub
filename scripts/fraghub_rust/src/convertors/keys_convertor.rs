// src/convertors/keys_convertor.rs

use pyo3::prelude::*;
use std::collections::HashMap;

/// Convert keys in metadata_dict based on the provided keys_dict and keys_list.
#[pyfunction]
pub fn convert_keys(
    metadata_dict: HashMap<String, String>,
    keys_dict: HashMap<String, String>,
    keys_list: Vec<String>
) -> HashMap<String, String> {

    let mut converted: HashMap<String, String> = HashMap::new();

    // Creating a dictionary comprehension equivalent that converts all keys from metadata to lower case
    for (key, val) in metadata_dict {
        let lower_key = key.to_lowercase();

        // Matches them with the keys available in keys_dict and keys_list.
        if let Some(mapped_key) = keys_dict.get(&lower_key) {
            if keys_list.contains(mapped_key) {
                converted.insert(mapped_key.clone(), val);
            }
        }
    }

    // After initial conversion, adds those missing keys to the converted dictionary with an empty string ("")
    for key in keys_list {
        converted.entry(key).or_insert_with(|| String::from(""));
    }

    converted
}