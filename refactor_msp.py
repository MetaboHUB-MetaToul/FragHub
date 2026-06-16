import re

with open('scripts/fraghub_rust/src/convertors/msp_to_dict.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyDict, PyList, PyAny};", "use pyo3::prelude::*;\nuse pyo3::types::{PyList, PyAny};\nuse crate::spectrum::Spectrum;")

content = content.replace("#[pyfunction]\n#[pyo3(signature = (final_msp_obj, keys_dict, keys_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")

content = content.replace("pub fn msp_to_dict_processing<'py>(", "pub fn msp_to_dict_processing(")
content = content.replace("-> PyResult<Bound<'py, PyList>> {", "-> PyResult<Vec<Spectrum>> {")

content = content.replace("let result_list = PyList::empty_bound(py);", "let mut result_list = Vec::new();")

old_tail = """        for parsed in parsed_chunk {
            let final_dict = PyDict::new_bound(py);
            for (k, v) in parsed.metadata {
                if let Some(mapped) = keys_dict.get(&k) {
                    if keys_list.contains(mapped) {
                        let _ = final_dict.set_item(mapped, v);
                    }
                }
            }

            if let Some(mapped_peak) = keys_dict.get("peaks") {
                let _ = final_dict.set_item(mapped_peak, parsed.peaks);
            } else {
                let _ = final_dict.set_item("PEAKS_LIST", parsed.peaks);
            }

            for key in &keys_list {
                if !final_dict.contains(key.as_str()).unwrap_or(false) { let _ = final_dict.set_item(key, ""); }
            }

            let _ = result_list.append(final_dict);
        }"""

new_tail = """        for parsed in parsed_chunk {
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
        }"""

content = content.replace(old_tail, new_tail)

with open('scripts/fraghub_rust/src/convertors/msp_to_dict.rs', 'w') as f:
    f.write(content)
