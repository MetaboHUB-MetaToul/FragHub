import re

with open('scripts/fraghub_rust/src/splitter.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyDict, PyList, PyAny};", "use pyo3::prelude::*;\nuse crate::spectrum::Spectrum;")

content = content.replace("// Fonction utilitaire pour reconstruire un DataFrame Pandas ultra-rapidement", "/*\n// Fonction utilitaire pour reconstruire un DataFrame Pandas ultra-rapidement")
content = content.replace("pandas.call_method(\"DataFrame\", (list,), Some(&kwargs))\n}", "pandas.call_method(\"DataFrame\", (list,), Some(&kwargs))\n}\n*/")

content = content.replace("#[pyfunction]\n#[pyo3(signature = (spectrum_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")
content = content.replace("pub fn split_pos_neg<'py>(", "pub fn split_pos_neg(")
content = content.replace("spectrum_list: &Bound<'py, PyList>,", "spectrum_list: &Vec<Spectrum>,")
content = content.replace("-> PyResult<(Bound<'py, PyList>, Bound<'py, PyList>)> {", "-> PyResult<(Vec<Spectrum>, Vec<Spectrum>)> {")

old_loop = """    let mut unique_inchikeys = HashSet::new();
    let pos_list = PyList::empty_bound(py);
    let neg_list = PyList::empty_bound(py);

    for item in spectrum_list.iter() {
        let dict = item.downcast::<PyDict>()?;

        // Stockage des Inchikeys uniques
        if let Ok(Some(inchikey)) = dict.get_item("INCHIKEY") {
            if let Ok(inchikey_str) = inchikey.extract::<String>() {
                unique_inchikeys.insert(inchikey_str);
            }
        }

        // Triage par pointeurs ! (Aucune donnée n'est dupliquée en RAM)
        if let Ok(Some(ionmode)) = dict.get_item("IONMODE") {
            if let Ok(ionmode_str) = ionmode.extract::<String>() {
                let lower = ionmode_str.to_lowercase();
                if lower == "positive" {
                    pos_list.append(&item)?;
                } else if lower == "negative" {
                    neg_list.append(&item)?;
                }
            }
        }
    }"""

new_loop = """    let mut unique_inchikeys = std::collections::HashSet::new();
    let mut pos_list = Vec::new();
    let mut neg_list = Vec::new();

    for spec in spectrum_list.iter() {
        let inchikey = spec.metadata.get("INCHIKEY").cloned().unwrap_or_default();
        if !inchikey.is_empty() {
            unique_inchikeys.insert(inchikey);
        }

        let ionmode = spec.metadata.get("IONMODE").cloned().unwrap_or_default().to_lowercase();
        if ionmode == "positive" {
            pos_list.push(spec.clone());
        } else if ionmode == "negative" {
            neg_list.push(spec.clone());
        }
    }"""

content = content.replace(old_loop, new_loop)

content = content.replace("#[pyfunction]\n#[pyo3(signature = (pos_list, neg_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")
content = content.replace("pub fn split_LC_GC<'py>(", "pub fn split_lc_gc(")
content = content.replace("pos_list: &Bound<'py, PyList>,\n    neg_list: &Bound<'py, PyList>,", "pos_list: &Vec<Spectrum>,\n    neg_list: &Vec<Spectrum>,")
content = content.replace("-> PyResult<(Bound<'py, PyList>, Bound<'py, PyList>, Bound<'py, PyList>, Bound<'py, PyList>)> {", "-> PyResult<(Vec<Spectrum>, Vec<Spectrum>, Vec<Spectrum>, Vec<Spectrum>)> {")

old_lc_gc = """    let partition_lc_gc = |list: &Bound<'py, PyList>| -> PyResult<(Bound<'py, PyList>, Bound<'py, PyList>)> {
        let lc_list = PyList::empty_bound(py);
        let gc_list = PyList::empty_bound(py);
        if list.len() > 0 {
            for item in list.iter() {
                let dict = item.downcast::<PyDict>()?;

                let mut is_gc = false;
                if let Ok(Some(instr)) = dict.get_item("INSTRUMENTTYPE") {
                    if let Ok(instr_str) = instr.extract::<String>() {
                        let upper = instr_str.to_uppercase();
                        if upper.contains("GC") || upper.contains("EI") {
                            is_gc = true;
                        }
                    }
                }

                if is_gc {
                    gc_list.append(&item)?;
                } else {
                    lc_list.append(&item)?;
                }
            }
        }
        Ok((lc_list, gc_list))
    };"""

new_lc_gc = """    let partition_lc_gc = |list: &Vec<Spectrum>| -> PyResult<(Vec<Spectrum>, Vec<Spectrum>)> {
        let mut lc_list = Vec::new();
        let mut gc_list = Vec::new();
        if list.len() > 0 {
            for spec in list.iter() {
                let instr = spec.metadata.get("INSTRUMENTTYPE").cloned().unwrap_or_default().to_uppercase();
                let is_gc = instr.contains("GC") || instr.contains("EI");

                if is_gc {
                    gc_list.push(spec.clone());
                } else {
                    lc_list.push(spec.clone());
                }
            }
        }
        Ok((lc_list, gc_list))
    };"""

content = content.replace(old_lc_gc, new_lc_gc)


content = content.replace("#[pyfunction]\n#[pyo3(signature = (pos_lc, pos_gc, neg_lc, neg_gc, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")
content = content.replace("pub fn exp_in_silico_splitter<'py>(", "pub fn exp_in_silico_splitter(")
content = content.replace("pos_lc: &Bound<'py, PyList>,\n    pos_gc: &Bound<'py, PyList>,\n    neg_lc: &Bound<'py, PyList>,\n    neg_gc: &Bound<'py, PyList>,", "pos_lc: &Vec<Spectrum>,\n    pos_gc: &Vec<Spectrum>,\n    neg_lc: &Vec<Spectrum>,\n    neg_gc: &Vec<Spectrum>,")

old_ret = """-> PyResult<(
    Bound<'py, PyList>, Bound<'py, PyList>,
Bound<'py, PyList>, Bound<'py, PyList>,
Bound<'py, PyList>, Bound<'py, PyList>,
Bound<'py, PyList>, Bound<'py, PyList>
)> {"""
new_ret = """-> PyResult<(
    Vec<Spectrum>, Vec<Spectrum>,
    Vec<Spectrum>, Vec<Spectrum>,
    Vec<Spectrum>, Vec<Spectrum>,
    Vec<Spectrum>, Vec<Spectrum>
)> {"""
content = content.replace(old_ret, new_ret)

old_split = """    // Fonction intégrée pour simuler les multiples appels de votre fonction Python "split_in_silico_exp"
    let emulate_split_in_silico_exp = |list: &Bound<'py, PyList>, text_true: &str, text_false: &str| -> PyResult<(Bound<'py, PyList>, Bound<'py, PyList>)> {
        let exp_list = PyList::empty_bound(py);
        let in_silico_list = PyList::empty_bound(py);
        let len = list.len();
        if len > 0 {
            for item in list.iter() {
                let dict = item.downcast::<PyDict>()?;

                if let Ok(Some(pred)) = dict.get_item("PREDICTED") {
                    if let Ok(pred_str) = pred.extract::<String>() {
                        let lower = pred_str.to_lowercase();
                        if lower == "true" {
                            in_silico_list.append(&item)?;
                        } else {
                            exp_list.append(&item)?;
                        }
                    } else {
                        exp_list.append(&item)?;
                    }
                } else {
                    exp_list.append(&item)?;
                }
            }"""

new_split = """    // Fonction intégrée pour simuler les multiples appels de votre fonction Python "split_in_silico_exp"
    let emulate_split_in_silico_exp = |list: &Vec<Spectrum>, text_true: &str, text_false: &str| -> PyResult<(Vec<Spectrum>, Vec<Spectrum>)> {
        let mut exp_list = Vec::new();
        let mut in_silico_list = Vec::new();
        let len = list.len();
        if len > 0 {
            for spec in list.iter() {
                let pred = spec.metadata.get("PREDICTED").cloned().unwrap_or_default().to_lowercase();
                if pred == "true" {
                    in_silico_list.push(spec.clone());
                } else {
                    exp_list.push(spec.clone());
                }
            }"""

content = content.replace(old_split, new_split)

with open('scripts/fraghub_rust/src/splitter.rs', 'w') as f:
    f.write(content)
