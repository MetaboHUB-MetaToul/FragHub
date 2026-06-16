import re

with open('scripts/fraghub_rust/src/report.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyDict, PyAny, PyList};", "use pyo3::prelude::*;\nuse pyo3::types::{PyDict};\nuse crate::spectrum::Spectrum;")

old_get_df = """// Fonction utilitaire pour extraire la taille et les INCHIKEYs uniques d'un DataFrame via PyO3

fn get_df_stats(list: &Bound<'_, PyAny>) -> PyResult<(usize, usize)> {
    let length: usize = list.len()?;
    let mut unique = 0;
    if length > 0 {
        if let Ok(l) = list.downcast::<PyList>() {
            let mut unique_set = std::collections::HashSet::new();
            for item in l.iter() {
                if let Ok(dict) = item.downcast::<PyDict>() {
                    if let Ok(Some(val)) = dict.get_item("INCHIKEY") {
                        let s = val.to_string();
                        if !s.is_empty() && s.to_lowercase() != "nan" {
                            unique_set.insert(s);
                        }
                    }
                }
            }
            unique = unique_set.len();
        }
    }
    Ok((length, unique))
}"""

new_get_df = """// Fonction utilitaire pour extraire la taille et les INCHIKEYs uniques d'un Vec<Spectrum>

fn get_df_stats(list: &Vec<Spectrum>) -> PyResult<(usize, usize)> {
    let length = list.len();
    let mut unique = 0;
    if length > 0 {
        let mut unique_set = std::collections::HashSet::new();
        for spec in list {
            if let Some(val) = spec.metadata.get("INCHIKEY") {
                let s = val.to_string();
                if !s.is_empty() && s.to_lowercase() != "nan" {
                    unique_set.insert(s);
                }
            }
        }
        unique = unique_set.len();
    }
    Ok((length, unique))
}"""

content = content.replace(old_get_df, new_get_df)

content = content.replace("#[pyfunction]\n#[pyo3(signature = (output_directory, date_str, parameters_dict, deletion_dict, pos_lc, pos_lc_insilico, pos_gc, pos_gc_insilico, neg_lc, neg_lc_insilico, neg_gc, neg_gc_insilico))]\n", "")

content = content.replace("pub fn generate_report_processing<'py>(", "pub fn generate_report_processing(")

content = content.replace("pos_lc: &Bound<'py, PyAny>,\n    pos_lc_insilico: &Bound<'py, PyAny>,\n    pos_gc: &Bound<'py, PyAny>,\n    pos_gc_insilico: &Bound<'py, PyAny>,\n    neg_lc: &Bound<'py, PyAny>,\n    neg_lc_insilico: &Bound<'py, PyAny>,\n    neg_gc: &Bound<'py, PyAny>,\n    neg_gc_insilico: &Bound<'py, PyAny>,",
                          "pos_lc: &Vec<Spectrum>,\n    pos_lc_insilico: &Vec<Spectrum>,\n    pos_gc: &Vec<Spectrum>,\n    pos_gc_insilico: &Vec<Spectrum>,\n    neg_lc: &Vec<Spectrum>,\n    neg_lc_insilico: &Vec<Spectrum>,\n    neg_gc: &Vec<Spectrum>,\n    neg_gc_insilico: &Vec<Spectrum>,")


with open('scripts/fraghub_rust/src/report.rs', 'w') as f:
    f.write(content)
