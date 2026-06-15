// src/csv_to_msp.rs
use pyo3::prelude::*;
use pyo3::types::{PyList, PyDict};

// Fonction pour extraire et nettoyer une valeur depuis le dictionnaire Python
fn get_string(dict: &Bound<'_, PyDict>, key: &str) -> String {
    if let Ok(Some(val)) = dict.get_item(key) {
        if let Ok(s) = val.extract::<String>() {
            let trimmed = s.trim();
            if trimmed.is_empty() || trimmed.eq_ignore_ascii_case("nan") {
                return "NOT FOUND".to_string();
            }
            return s.to_string();
        } else if let Ok(num) = val.extract::<f64>() {
            if !num.is_nan() { return num.to_string(); }
        } else if let Ok(num) = val.extract::<i64>() {
            return num.to_string();
        }
    }
    "NOT FOUND".to_string()
}

fn list_to_msp<'py>(
    py: Python<'py>,
    data_list: &Bound<'py, PyList>,
    name: &str,
    progress_callback: &Option<PyObject>,
    total_items_callback: &Option<PyObject>,
    prefix_callback: &Option<PyObject>,
    item_type_callback: &Option<PyObject>,
) -> PyResult<Vec<String>> {

    let len = data_list.len();
    if len == 0 {
        return Ok(Vec::new());
    }

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Formatting {} to MSP:", name),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("rows",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    let mut spectrum_list = Vec::with_capacity(len);

    for i in 0..len {
        let item = data_list.get_item(i)?;
        let dict = item.downcast::<PyDict>()?;

        let comments = format!("FILENAME={}; FILEHASH={}; PREDICTED={}; SPLASH={}; SPECTRUMID={}; RESOLUTION={}; SYNON={}; FRAGMENTATIONMODE={}; AVERAGEMASS={}; ENTROPY={}; ONTOLOGIES = \"CLASSYFIRE_SUPERCLASS={}, CLASSYFIRE_CLASS = {}, CLASSYFIRE_SUBCLASS = {}, NPCLASS_PATHWAY = {}, NPCLASS_SUPERCLASS = {}, NPCLASS_CLASS = {}\"",
                               get_string(dict, "FILENAME"), get_string(dict, "FILEHASH"), get_string(dict, "PREDICTED"),
                               get_string(dict, "SPLASH"), get_string(dict, "SPECTRUMID"), get_string(dict, "RESOLUTION"),
                               get_string(dict, "SYNON"), get_string(dict, "FRAGMENTATIONMODE"), get_string(dict, "AVERAGEMASS"),
                               get_string(dict, "ENTROPY"), get_string(dict, "CLASSYFIRE_SUPERCLASS"), get_string(dict, "CLASSYFIRE_CLASS"),
                               get_string(dict, "CLASSYFIRE_SUBCLASS"), get_string(dict, "NPCLASS_PATHWAY"), get_string(dict, "NPCLASS_SUPERCLASS"),
                               get_string(dict, "NPCLASS_CLASS")
        );

        let mut spectrum = String::with_capacity(1024);
        spectrum.push_str("NAME: "); spectrum.push_str(&get_string(dict, "NAME")); spectrum.push('\n');
        spectrum.push_str("PRECURSORMZ: "); spectrum.push_str(&get_string(dict, "PRECURSORMZ")); spectrum.push('\n');
        spectrum.push_str("PRECURSORTYPE: "); spectrum.push_str(&get_string(dict, "PRECURSORTYPE")); spectrum.push('\n');
        spectrum.push_str("FORMULA: "); spectrum.push_str(&get_string(dict, "FORMULA")); spectrum.push('\n');
        spectrum.push_str("INCHIKEY: "); spectrum.push_str(&get_string(dict, "INCHIKEY")); spectrum.push('\n');
        spectrum.push_str("INCHI: "); spectrum.push_str(&get_string(dict, "INCHI")); spectrum.push('\n');
        spectrum.push_str("SMILES: "); spectrum.push_str(&get_string(dict, "SMILES")); spectrum.push('\n');
        spectrum.push_str("RT: "); spectrum.push_str(&get_string(dict, "RT")); spectrum.push('\n');
        spectrum.push_str("IONMODE: "); spectrum.push_str(&get_string(dict, "IONMODE")); spectrum.push('\n');
        spectrum.push_str("INSTRUMENTTYPE: "); spectrum.push_str(&get_string(dict, "INSTRUMENTTYPE")); spectrum.push('\n');
        spectrum.push_str("INSTRUMENT: "); spectrum.push_str(&get_string(dict, "INSTRUMENT")); spectrum.push('\n');
        spectrum.push_str("COLLISIONENERGY: "); spectrum.push_str(&get_string(dict, "COLLISIONENERGY")); spectrum.push('\n');
        spectrum.push_str("EXACTMASS: "); spectrum.push_str(&get_string(dict, "EXACTMASS")); spectrum.push('\n');
        spectrum.push_str("IONIZATION: "); spectrum.push_str(&get_string(dict, "IONIZATION")); spectrum.push('\n');
        spectrum.push_str("MSLEVEL: "); spectrum.push_str(&get_string(dict, "MSLEVEL")); spectrum.push('\n');
        spectrum.push_str("COMMENT: "); spectrum.push_str(&comments); spectrum.push('\n');
        spectrum.push_str("NUM PEAKS: "); spectrum.push_str(&get_string(dict, "NUM PEAKS")); spectrum.push('\n');

        let peaks = get_string(dict, "PEAKS_LIST");
        if peaks != "NOT FOUND" { spectrum.push_str(&peaks); }
        spectrum.push('\n');

        spectrum_list.push(spectrum);

        if let Some(cb) = progress_callback {
            if (i + 1) % 1000 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    Ok(spectrum_list)
}

#[pyfunction]
#[pyo3(signature = (pos_lc_df, pos_lc_df_insilico, pos_gc_df, pos_gc_df_insilico, neg_lc_df, neg_lc_df_insilico, neg_gc_df, neg_gc_df_insilico, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
#[allow(clippy::too_many_arguments)]
pub fn csv_to_msp_processing<'py>(
    py: Python<'py>, pos_lc_df: Bound<'py, PyList>, pos_lc_df_insilico: Bound<'py, PyList>, pos_gc_df: Bound<'py, PyList>, pos_gc_df_insilico: Bound<'py, PyList>, neg_lc_df: Bound<'py, PyList>, neg_lc_df_insilico: Bound<'py, PyList>, neg_gc_df: Bound<'py, PyList>, neg_gc_df_insilico: Bound<'py, PyList>, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<(Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>)> {
    let mut sleep = || std::thread::sleep(std::time::Duration::from_millis(100));

    sleep(); let pos_lc = list_to_msp(py, &pos_lc_df, "POS_LC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let pos_lc_in = list_to_msp(py, &pos_lc_df_insilico, "POS_LC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let pos_gc = list_to_msp(py, &pos_gc_df, "POS_GC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let pos_gc_in = list_to_msp(py, &pos_gc_df_insilico, "POS_GC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let neg_lc = list_to_msp(py, &neg_lc_df, "NEG_LC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let neg_lc_in = list_to_msp(py, &neg_lc_df_insilico, "NEG_LC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let neg_gc = list_to_msp(py, &neg_gc_df, "NEG_GC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); let neg_gc_in = list_to_msp(py, &neg_gc_df_insilico, "NEG_GC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    Ok((pos_lc, pos_lc_in, pos_gc, pos_gc_in, neg_lc, neg_lc_in, neg_gc, neg_gc_in))
}