// src/csv_to_msp.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;

// Fonction pour extraire et nettoyer une valeur depuis le dictionnaire Python
fn get_string(spec: &Spectrum, key: &str) -> String {
    if key == "PEAKS_LIST" {
        if spec.peaks.is_empty() { return "NOT FOUND".to_string(); }
        let mut peaks_str = String::with_capacity(spec.peaks.len() * 20);
        for (i, &(mz, int)) in spec.peaks.iter().enumerate() {
            if i > 0 { peaks_str.push('\n'); }
            peaks_str.push_str(&format!("{} {}", mz, int));
        }
        return peaks_str;
    }
    if let Some(val) = spec.metadata.get(key) {
        let trimmed = val.trim();
        if trimmed.is_empty() || trimmed.eq_ignore_ascii_case("nan") {
            return "NOT FOUND".to_string();
        }
        return val.clone();
    }
    "NOT FOUND".to_string()
}

fn list_to_msp<'py>(
    py: Python,
    data_list: &Vec<Spectrum>,
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

    for (i, spec) in data_list.iter().enumerate() {
        let comments = format!("FILENAME={}; FILEHASH={}; PREDICTED={}; SPLASH={}; SPECTRUMID={}; RESOLUTION={}; SYNON={}; FRAGMENTATIONMODE={}; AVERAGEMASS={}; ENTROPY={}; ONTOLOGIES = \"CLASSYFIRE_SUPERCLASS={}, CLASSYFIRE_CLASS = {}, CLASSYFIRE_SUBCLASS = {}, NPCLASS_PATHWAY = {}, NPCLASS_SUPERCLASS = {}, NPCLASS_CLASS = {}\"",
                               get_string(spec, "FILENAME"), get_string(spec, "FILEHASH"), get_string(spec, "PREDICTED"),
                               get_string(spec, "SPLASH"), get_string(spec, "SPECTRUMID"), get_string(spec, "RESOLUTION"),
                               get_string(spec, "SYNON"), get_string(spec, "FRAGMENTATIONMODE"), get_string(spec, "AVERAGEMASS"),
                               get_string(spec, "ENTROPY"), get_string(spec, "CLASSYFIRE_SUPERCLASS"), get_string(spec, "CLASSYFIRE_CLASS"),
                               get_string(spec, "CLASSYFIRE_SUBCLASS"), get_string(spec, "NPCLASS_PATHWAY"), get_string(spec, "NPCLASS_SUPERCLASS"),
                               get_string(spec, "NPCLASS_CLASS")
        );

        let mut spectrum = String::with_capacity(1024);
        spectrum.push_str("NAME: "); spectrum.push_str(&get_string(spec, "NAME")); spectrum.push('\n');
        spectrum.push_str("PRECURSORMZ: "); spectrum.push_str(&get_string(spec, "PRECURSORMZ")); spectrum.push('\n');
        spectrum.push_str("PRECURSORTYPE: "); spectrum.push_str(&get_string(spec, "PRECURSORTYPE")); spectrum.push('\n');
        spectrum.push_str("FORMULA: "); spectrum.push_str(&get_string(spec, "FORMULA")); spectrum.push('\n');
        spectrum.push_str("INCHIKEY: "); spectrum.push_str(&get_string(spec, "INCHIKEY")); spectrum.push('\n');
        spectrum.push_str("INCHI: "); spectrum.push_str(&get_string(spec, "INCHI")); spectrum.push('\n');
        spectrum.push_str("SMILES: "); spectrum.push_str(&get_string(spec, "SMILES")); spectrum.push('\n');
        spectrum.push_str("RT: "); spectrum.push_str(&get_string(spec, "RT")); spectrum.push('\n');
        spectrum.push_str("IONMODE: "); spectrum.push_str(&get_string(spec, "IONMODE")); spectrum.push('\n');
        spectrum.push_str("INSTRUMENTTYPE: "); spectrum.push_str(&get_string(spec, "INSTRUMENTTYPE")); spectrum.push('\n');
        spectrum.push_str("INSTRUMENT: "); spectrum.push_str(&get_string(spec, "INSTRUMENT")); spectrum.push('\n');
        spectrum.push_str("COLLISIONENERGY: "); spectrum.push_str(&get_string(spec, "COLLISIONENERGY")); spectrum.push('\n');
        spectrum.push_str("EXACTMASS: "); spectrum.push_str(&get_string(spec, "EXACTMASS")); spectrum.push('\n');
        spectrum.push_str("IONIZATION: "); spectrum.push_str(&get_string(spec, "IONIZATION")); spectrum.push('\n');
        spectrum.push_str("MSLEVEL: "); spectrum.push_str(&get_string(spec, "MSLEVEL")); spectrum.push('\n');
        spectrum.push_str("COMMENT: "); spectrum.push_str(&comments); spectrum.push('\n');
        spectrum.push_str("NUM PEAKS: "); spectrum.push_str(&get_string(spec, "NUM PEAKS")); spectrum.push('\n');

        let peaks = get_string(spec, "PEAKS_LIST");
        if peaks != "NOT FOUND" { spectrum.push_str(&peaks); }
        spectrum.push('\n');

        spectrum_list.push(spectrum);

        if let Some(cb) = progress_callback {
            if (i + 1) % 1000 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    Ok(spectrum_list)
}

#[allow(clippy::too_many_arguments)]
pub fn csv_to_msp_processing(
    py: Python, pos_lc_df: Vec<Spectrum>, pos_lc_df_insilico: Vec<Spectrum>, pos_gc_df: Vec<Spectrum>, pos_gc_df_insilico: Vec<Spectrum>, neg_lc_df: Vec<Spectrum>, neg_lc_df_insilico: Vec<Spectrum>, neg_gc_df: Vec<Spectrum>, neg_gc_df_insilico: Vec<Spectrum>, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
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