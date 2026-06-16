// src/splitter.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;

pub fn split_pos_neg(
    py: Python,
    spectrum_list: &Vec<Spectrum>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Vec<Spectrum>, Vec<Spectrum>)> {
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Splitting POS/NEG:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    let total_items = spectrum_list.len();

    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    let mut unique_inchikeys = std::collections::HashSet::new();
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
    }

    if let Some(cb) = &progress_callback { cb.call1(py, (pos_list.len(),))?; }
    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    Ok((pos_list, neg_list))
}

pub fn split_lc_gc(
    py: Python,
    pos_list: &Vec<Spectrum>,
    neg_list: &Vec<Spectrum>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Vec<Spectrum>, Vec<Spectrum>, Vec<Spectrum>, Vec<Spectrum>)> {
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Splitting LC/GC:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    let pos_len = pos_list.len();
    let neg_len = neg_list.len();
    let total_rows = pos_len + neg_len;

    if let Some(cb) = &total_items_callback { cb.call1(py, (total_rows, 0))?; }

    let partition_lc_gc = |list: &Vec<Spectrum>| -> PyResult<(Vec<Spectrum>, Vec<Spectrum>)> {
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
    };

    let (pos_lc_list, pos_gc_list) = partition_lc_gc(&pos_list)?;
    if let Some(cb) = &progress_callback { cb.call1(py, (pos_gc_list.len(),))?; }
    if let Some(cb) = &progress_callback { cb.call1(py, (pos_len,))?; }

    let (neg_lc_list, neg_gc_list) = partition_lc_gc(&neg_list)?;
    if let Some(cb) = &progress_callback { cb.call1(py, (pos_len + neg_gc_list.len(),))?; }
    if let Some(cb) = &progress_callback { cb.call1(py, (total_rows,))?; }

    Ok((pos_lc_list, pos_gc_list, neg_lc_list, neg_gc_list))
}

pub fn exp_in_silico_splitter(
    py: Python,
    pos_lc: &Vec<Spectrum>,
    pos_gc: &Vec<Spectrum>,
    neg_lc: &Vec<Spectrum>,
    neg_gc: &Vec<Spectrum>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(
    Vec<Spectrum>, Vec<Spectrum>,
    Vec<Spectrum>, Vec<Spectrum>,
    Vec<Spectrum>, Vec<Spectrum>,
    Vec<Spectrum>, Vec<Spectrum>
)> {

    // Fonction intégrée pour simuler les multiples appels de votre fonction Python "split_in_silico_exp"
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
            }

            // Émulation UI : appel pour "In Silico"
            if let Some(cb) = &prefix_callback { cb.call1(py, (format!("{}:", text_true),))?; }
            if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }
            if let Some(cb) = &total_items_callback { cb.call1(py, (len, 0))?; }
            if let Some(cb) = &progress_callback { cb.call1(py, (in_silico_list.len(),))?; }

            // Émulation UI : appel pour "Experimental"
            if let Some(cb) = &prefix_callback { cb.call1(py, (format!("{}:", text_false),))?; }
            if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }
            if let Some(cb) = &total_items_callback { cb.call1(py, (len, 0))?; }
            if let Some(cb) = &progress_callback { cb.call1(py, (exp_list.len(),))?; }
        }
        Ok((exp_list, in_silico_list))
    };

    let (pos_lc_exp, pos_lc_in_silico) = emulate_split_in_silico_exp(&pos_lc, "POS_LC_In_Silico", "POS_LC_Exp")?;
    let (pos_gc_exp, pos_gc_in_silico) = emulate_split_in_silico_exp(&pos_gc, "POS_GC_In_Silico", "POS_GC_Exp")?;
    let (neg_lc_exp, neg_lc_in_silico) = emulate_split_in_silico_exp(&neg_lc, "NEG_LC_In_Silico", "NEG_LC_Exp")?;
    let (neg_gc_exp, neg_gc_in_silico) = emulate_split_in_silico_exp(&neg_gc, "NEG_GC_In_Silico", "NEG_GC_Exp")?;

    Ok((pos_lc_exp, pos_lc_in_silico, pos_gc_exp, pos_gc_in_silico, neg_lc_exp, neg_lc_in_silico, neg_gc_exp, neg_gc_in_silico))
}
