// src/csv_to_msp.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};

// Fonction utilitaire ultra-rapide pour extraire ou renvoyer "NOT FOUND"
fn get_str<'py>(dict: &Bound<'py, PyDict>, key: &str) -> String {
    if let Ok(Some(val)) = dict.get_item(key) {
        let s = val.extract::<String>().unwrap_or_else(|_| val.to_string());
        if !s.trim().is_empty() && s.to_lowercase() != "nan" {
            return s;
        }
    }
    "NOT FOUND".to_string()
}

fn dataframe_to_msp<'py>(
    py: Python<'py>,
    df: &Bound<'py, PyAny>,
    name: &str,
    progress_callback: &Option<PyObject>,
    total_items_callback: &Option<PyObject>,
    prefix_callback: &Option<PyObject>,
    item_type_callback: &Option<PyObject>,
) -> PyResult<Vec<String>> {

    let len: usize = df.call_method0("__len__")?.extract()?;
    if len == 0 {
        return Ok(Vec::new());
    }

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Formatting {} to MSP:", name),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("rows",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    // Extraction des dictionnaires depuis Pandas
    let dict_list_py = df.call_method1("to_dict", ("records",))?;
    let records = dict_list_py.downcast::<PyList>()?;

    let mut spectrum_list = Vec::with_capacity(len);

    for i in 0..len {
        let item = records.get_item(i).unwrap();
        let dict = item.downcast::<PyDict>()?;

        // Reconstitution stricte de l'f-string Python de format_comments
        let comments = format!("FILENAME={}; FILEHASH={}; PREDICTED={}; SPLASH={}; SPECTRUMID={}; RESOLUTION={}; SYNON={}; FRAGMENTATIONMODE={}; AVERAGEMASS={}; ENTROPY={}; ONTOLOGIES = \"CLASSYFIRE_SUPERCLASS={}, CLASSYFIRE_CLASS = {}, CLASSYFIRE_SUBCLASS = {}, NPCLASS_PATHWAY = {}, NPCLASS_SUPERCLASS = {}, NPCLASS_CLASS = {}\"",
                               get_str(&dict, "FILENAME"), get_str(&dict, "FILEHASH"), get_str(&dict, "PREDICTED"), get_str(&dict, "SPLASH"), get_str(&dict, "SPECTRUMID"), get_str(&dict, "RESOLUTION"), get_str(&dict, "SYNON"), get_str(&dict, "FRAGMENTATIONMODE"), get_str(&dict, "AVERAGEMASS"), get_str(&dict, "ENTROPY"),
                               get_str(&dict, "CLASSYFIRE_SUPERCLASS"), get_str(&dict, "CLASSYFIRE_CLASS"), get_str(&dict, "CLASSYFIRE_SUBCLASS"), get_str(&dict, "NPCLASS_PATHWAY"), get_str(&dict, "NPCLASS_SUPERCLASS"), get_str(&dict, "NPCLASS_CLASS")
        );

        // Buffer alloué à l'avance pour éviter la fragmentation mémoire
        let mut spectrum = String::with_capacity(1024);
        spectrum.push_str("NAME: "); spectrum.push_str(&get_str(&dict, "NAME")); spectrum.push('\n');
        spectrum.push_str("PRECURSORMZ: "); spectrum.push_str(&get_str(&dict, "PRECURSORMZ")); spectrum.push('\n');
        spectrum.push_str("PRECURSORTYPE: "); spectrum.push_str(&get_str(&dict, "PRECURSORTYPE")); spectrum.push('\n');
        spectrum.push_str("FORMULA: "); spectrum.push_str(&get_str(&dict, "FORMULA")); spectrum.push('\n');
        spectrum.push_str("INCHIKEY: "); spectrum.push_str(&get_str(&dict, "INCHIKEY")); spectrum.push('\n');
        spectrum.push_str("INCHI: "); spectrum.push_str(&get_str(&dict, "INCHI")); spectrum.push('\n');
        spectrum.push_str("SMILES: "); spectrum.push_str(&get_str(&dict, "SMILES")); spectrum.push('\n');
        spectrum.push_str("RT: "); spectrum.push_str(&get_str(&dict, "RT")); spectrum.push('\n');
        spectrum.push_str("IONMODE: "); spectrum.push_str(&get_str(&dict, "IONMODE")); spectrum.push('\n');
        spectrum.push_str("INSTRUMENTTYPE: "); spectrum.push_str(&get_str(&dict, "INSTRUMENTTYPE")); spectrum.push('\n');
        spectrum.push_str("INSTRUMENT: "); spectrum.push_str(&get_str(&dict, "INSTRUMENT")); spectrum.push('\n');
        spectrum.push_str("COLLISIONENERGY: "); spectrum.push_str(&get_str(&dict, "COLLISIONENERGY")); spectrum.push('\n');
        spectrum.push_str("EXACTMASS: "); spectrum.push_str(&get_str(&dict, "EXACTMASS")); spectrum.push('\n');
        spectrum.push_str("IONIZATION: "); spectrum.push_str(&get_str(&dict, "IONIZATION")); spectrum.push('\n');
        spectrum.push_str("MSLEVEL: "); spectrum.push_str(&get_str(&dict, "MSLEVEL")); spectrum.push('\n');
        spectrum.push_str("COMMENT: "); spectrum.push_str(&comments); spectrum.push('\n');
        spectrum.push_str("NUM PEAKS: "); spectrum.push_str(&get_str(&dict, "NUM PEAKS")); spectrum.push('\n');

        if let Ok(Some(peaks_val)) = dict.get_item("PEAKS_LIST") {
            let peaks = peaks_val.extract::<String>().unwrap_or_else(|_| peaks_val.to_string());
            if peaks != "nan" {
                spectrum.push_str(&peaks);
            }
        }
        spectrum.push('\n');

        spectrum_list.push(spectrum);

        // Throttle progress_callback pour ne pas freezer l'interface
        if let Some(cb) = progress_callback {
            if (i + 1) % 1000 == 0 || i == len - 1 {
                cb.call1(py, (i + 1,))?;
            }
        }
    }

    Ok(spectrum_list)
}

#[pyfunction]
#[pyo3(signature = (pos_lc_df, pos_lc_df_insilico, pos_gc_df, pos_gc_df_insilico, neg_lc_df, neg_lc_df_insilico, neg_gc_df, neg_gc_df_insilico, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
#[allow(clippy::too_many_arguments)]
pub fn csv_to_msp_processing<'py>(
    py: Python<'py>,
    pos_lc_df: Bound<'py, PyAny>,
    pos_lc_df_insilico: Bound<'py, PyAny>,
    pos_gc_df: Bound<'py, PyAny>,
    pos_gc_df_insilico: Bound<'py, PyAny>,
    neg_lc_df: Bound<'py, PyAny>,
    neg_lc_df_insilico: Bound<'py, PyAny>,
    neg_gc_df: Bound<'py, PyAny>,
    neg_gc_df_insilico: Bound<'py, PyAny>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(
    Vec<String>, Vec<String>, Vec<String>, Vec<String>,
    Vec<String>, Vec<String>, Vec<String>, Vec<String>
)> {

    // Reproduction du time.sleep(0.1) pour l'UI
    let mut sleep = || std::thread::sleep(std::time::Duration::from_millis(100));

    sleep();
    let pos_lc = dataframe_to_msp(py, &pos_lc_df, "POS_LC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let pos_lc_in = dataframe_to_msp(py, &pos_lc_df_insilico, "POS_LC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let pos_gc = dataframe_to_msp(py, &pos_gc_df, "POS_GC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let pos_gc_in = dataframe_to_msp(py, &pos_gc_df_insilico, "POS_GC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let neg_lc = dataframe_to_msp(py, &neg_lc_df, "NEG_LC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let neg_lc_in = dataframe_to_msp(py, &neg_lc_df_insilico, "NEG_LC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let neg_gc = dataframe_to_msp(py, &neg_gc_df, "NEG_GC", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    sleep();
    let neg_gc_in = dataframe_to_msp(py, &neg_gc_df_insilico, "NEG_GC_insilico", &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;

    Ok((pos_lc, pos_lc_in, pos_gc, pos_gc_in, neg_lc, neg_lc_in, neg_gc, neg_gc_in))
}