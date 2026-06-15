// src/splitter.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};
use std::collections::HashSet;

// Fonction utilitaire pour reconstruire un DataFrame Pandas ultra-rapidement
fn build_dataframe<'py>(py: Python<'py>, list: Bound<'py, PyList>, columns: Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    let pandas = py.import_bound("pandas")?;
    let kwargs = PyDict::new_bound(py);
    kwargs.set_item("columns", columns)?;
    pandas.call_method("DataFrame", (list,), Some(&kwargs))
}

#[pyfunction]
#[pyo3(signature = (concatenate_df, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn split_pos_neg<'py>(
    py: Python<'py>,
    concatenate_df: Bound<'py, PyAny>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>)> {
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Splitting POS/NEG:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    let original_columns = concatenate_df.getattr("columns")?;
    let dict_list_py = concatenate_df.call_method1("to_dict", ("records",))?;
    let records = dict_list_py.downcast::<PyList>()?;
    let total_items = records.len();

    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    let mut unique_inchikeys = HashSet::new();
    let pos_list = PyList::empty_bound(py);
    let neg_list = PyList::empty_bound(py);

    for i in 0..total_items {
        let item = records.get_item(i).unwrap();
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
    }

    // Mise à jour de votre fichier global_report en Python !
    if let Ok(global_report) = py.import_bound("scripts.global_report") {
        if let Ok(report_dict) = global_report.getattr("report_dict") {
            if let Ok(dict) = report_dict.downcast::<PyDict>() {
                dict.set_item("TOTAL_unique_inchikey", unique_inchikeys.len())?;
            }
        }
    }

    if let Some(cb) = &progress_callback { cb.call1(py, (pos_list.len(),))?; }
    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    let pos_df = build_dataframe(py, pos_list, original_columns.clone())?;
    let neg_df = build_dataframe(py, neg_list, original_columns)?;

    Ok((pos_df, neg_df))
}

#[pyfunction]
#[pyo3(signature = (pos_df, neg_df, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn split_LC_GC<'py>(
    py: Python<'py>,
    pos_df: Bound<'py, PyAny>,
    neg_df: Bound<'py, PyAny>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Bound<'py, PyAny>, Bound<'py, PyAny>, Bound<'py, PyAny>, Bound<'py, PyAny>)> {
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Splitting LC/GC:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    let pos_len: usize = pos_df.call_method0("__len__")?.extract()?;
    let neg_len: usize = neg_df.call_method0("__len__")?.extract()?;
    let total_rows = pos_len + neg_len;

    if let Some(cb) = &total_items_callback { cb.call1(py, (total_rows, 0))?; }

    let partition_lc_gc = |df: &Bound<'py, PyAny>| -> PyResult<(Bound<'py, PyList>, Bound<'py, PyList>)> {
        let lc_list = PyList::empty_bound(py);
        let gc_list = PyList::empty_bound(py);

        let len: usize = df.call_method0("__len__")?.extract()?;
        if len > 0 {
            let dict_list_py = df.call_method1("to_dict", ("records",))?;
            let records = dict_list_py.downcast::<PyList>()?;

            for i in 0..records.len() {
                let item = records.get_item(i).unwrap();
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
    };

    let (pos_lc_list, pos_gc_list) = partition_lc_gc(&pos_df)?;
    if let Some(cb) = &progress_callback { cb.call1(py, (pos_gc_list.len(),))?; }
    if let Some(cb) = &progress_callback { cb.call1(py, (pos_len,))?; }

    let (neg_lc_list, neg_gc_list) = partition_lc_gc(&neg_df)?;
    if let Some(cb) = &progress_callback { cb.call1(py, (pos_len + neg_gc_list.len(),))?; }
    if let Some(cb) = &progress_callback { cb.call1(py, (total_rows,))?; }

    let columns = pos_df.getattr("columns")?;
    let pos_lc = build_dataframe(py, pos_lc_list, columns.clone())?;
    let pos_gc = build_dataframe(py, pos_gc_list, columns.clone())?;
    let neg_lc = build_dataframe(py, neg_lc_list, columns.clone())?;
    let neg_gc = build_dataframe(py, neg_gc_list, columns)?;

    Ok((pos_lc, pos_gc, neg_lc, neg_gc))
}

#[pyfunction]
#[pyo3(signature = (pos_lc, pos_gc, neg_lc, neg_gc, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn exp_in_silico_splitter<'py>(
    py: Python<'py>,
    pos_lc: Bound<'py, PyAny>,
    pos_gc: Bound<'py, PyAny>,
    neg_lc: Bound<'py, PyAny>,
    neg_gc: Bound<'py, PyAny>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(
    Bound<'py, PyAny>, Bound<'py, PyAny>, // POS_LC_Exp, POS_LC_InSilico
    Bound<'py, PyAny>, Bound<'py, PyAny>, // POS_GC_Exp, POS_GC_InSilico
    Bound<'py, PyAny>, Bound<'py, PyAny>, // NEG_LC_Exp, NEG_LC_InSilico
    Bound<'py, PyAny>, Bound<'py, PyAny>  // NEG_GC_Exp, NEG_GC_InSilico
)> {

    // Fonction intégrée pour simuler les multiples appels de votre fonction Python "split_in_silico_exp"
    let mut emulate_split_in_silico_exp = |df: &Bound<'py, PyAny>, text_true: &str, text_false: &str| -> PyResult<(Bound<'py, PyList>, Bound<'py, PyList>)> {
        let exp_list = PyList::empty_bound(py);
        let in_silico_list = PyList::empty_bound(py);

        let len: usize = df.call_method0("__len__")?.extract()?;
        if len > 0 {
            let dict_list_py = df.call_method1("to_dict", ("records",))?;
            let records = dict_list_py.downcast::<PyList>()?;

            for i in 0..records.len() {
                let item = records.get_item(i).unwrap();
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

    let columns = pos_lc.getattr("columns")?;

    let out1 = build_dataframe(py, pos_lc_exp, columns.clone())?;
    let out2 = build_dataframe(py, pos_lc_in_silico, columns.clone())?;
    let out3 = build_dataframe(py, pos_gc_exp, columns.clone())?;
    let out4 = build_dataframe(py, pos_gc_in_silico, columns.clone())?;
    let out5 = build_dataframe(py, neg_lc_exp, columns.clone())?;
    let out6 = build_dataframe(py, neg_lc_in_silico, columns.clone())?;
    let out7 = build_dataframe(py, neg_gc_exp, columns.clone())?;
    let out8 = build_dataframe(py, neg_gc_in_silico, columns)?;

    Ok((out1, out2, out3, out4, out5, out6, out7, out8))
}