import re

with open('scripts/fraghub_rust/src/csv_to_msp.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyList, PyDict};", "use pyo3::prelude::*;\nuse crate::spectrum::Spectrum;")

content = content.replace("fn get_string(dict: &Bound<'_, PyDict>, key: &str) -> String {", "fn get_string(spec: &Spectrum, key: &str) -> String {")

old_get_string = """    if let Ok(Some(val)) = dict.get_item(key) {
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
    "NOT FOUND".to_string()"""

new_get_string = """    if key == "PEAKS_LIST" {
        if spec.peaks.is_empty() { return "NOT FOUND".to_string(); }
        let mut peaks_str = String::with_capacity(spec.peaks.len() * 20);
        for (i, &(mz, int)) in spec.peaks.iter().enumerate() {
            if i > 0 { peaks_str.push('\\n'); }
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
    "NOT FOUND".to_string()"""
content = content.replace(old_get_string, new_get_string)

content = content.replace("data_list: &Bound<'py, PyList>,", "data_list: &Vec<Spectrum>,")

old_loop = """    for i in 0..len {
        let item = data_list.get_item(i)?;
        let dict = item.downcast::<PyDict>()?;

        let comments = format!("FILENAME={}; FILEHASH={}; PREDICTED={}; SPLASH={}; SPECTRUMID={}; RESOLUTION={}; SYNON={}; FRAGMENTATIONMODE={}; AVERAGEMASS={}; ENTROPY={}; ONTOLOGIES = \\"CLASSYFIRE_SUPERCLASS={}, CLASSYFIRE_CLASS = {}, CLASSYFIRE_SUBCLASS = {}, NPCLASS_PATHWAY = {}, NPCLASS_SUPERCLASS = {}, NPCLASS_CLASS = {}\\"",
                               get_string(dict, "FILENAME"), get_string(dict, "FILEHASH"), get_string(dict, "PREDICTED"),
                               get_string(dict, "SPLASH"), get_string(dict, "SPECTRUMID"), get_string(dict, "RESOLUTION"),
                               get_string(dict, "SYNON"), get_string(dict, "FRAGMENTATIONMODE"), get_string(dict, "AVERAGEMASS"),
                               get_string(dict, "ENTROPY"), get_string(dict, "CLASSYFIRE_SUPERCLASS"), get_string(dict, "CLASSYFIRE_CLASS"),
                               get_string(dict, "CLASSYFIRE_SUBCLASS"), get_string(dict, "NPCLASS_PATHWAY"), get_string(dict, "NPCLASS_SUPERCLASS"),
                               get_string(dict, "NPCLASS_CLASS")
        );

        let mut spectrum = String::with_capacity(1024);
        spectrum.push_str("NAME: "); spectrum.push_str(&get_string(dict, "NAME")); spectrum.push('\\n');
        spectrum.push_str("PRECURSORMZ: "); spectrum.push_str(&get_string(dict, "PRECURSORMZ")); spectrum.push('\\n');
        spectrum.push_str("PRECURSORTYPE: "); spectrum.push_str(&get_string(dict, "PRECURSORTYPE")); spectrum.push('\\n');
        spectrum.push_str("FORMULA: "); spectrum.push_str(&get_string(dict, "FORMULA")); spectrum.push('\\n');
        spectrum.push_str("INCHIKEY: "); spectrum.push_str(&get_string(dict, "INCHIKEY")); spectrum.push('\\n');
        spectrum.push_str("INCHI: "); spectrum.push_str(&get_string(dict, "INCHI")); spectrum.push('\\n');
        spectrum.push_str("SMILES: "); spectrum.push_str(&get_string(dict, "SMILES")); spectrum.push('\\n');
        spectrum.push_str("RT: "); spectrum.push_str(&get_string(dict, "RT")); spectrum.push('\\n');
        spectrum.push_str("IONMODE: "); spectrum.push_str(&get_string(dict, "IONMODE")); spectrum.push('\\n');
        spectrum.push_str("INSTRUMENTTYPE: "); spectrum.push_str(&get_string(dict, "INSTRUMENTTYPE")); spectrum.push('\\n');
        spectrum.push_str("INSTRUMENT: "); spectrum.push_str(&get_string(dict, "INSTRUMENT")); spectrum.push('\\n');
        spectrum.push_str("COLLISIONENERGY: "); spectrum.push_str(&get_string(dict, "COLLISIONENERGY")); spectrum.push('\\n');
        spectrum.push_str("EXACTMASS: "); spectrum.push_str(&get_string(dict, "EXACTMASS")); spectrum.push('\\n');
        spectrum.push_str("IONIZATION: "); spectrum.push_str(&get_string(dict, "IONIZATION")); spectrum.push('\\n');
        spectrum.push_str("MSLEVEL: "); spectrum.push_str(&get_string(dict, "MSLEVEL")); spectrum.push('\\n');
        spectrum.push_str("COMMENT: "); spectrum.push_str(&comments); spectrum.push('\\n');
        spectrum.push_str("NUM PEAKS: "); spectrum.push_str(&get_string(dict, "NUM PEAKS")); spectrum.push('\\n');

        let peaks = get_string(dict, "PEAKS_LIST");
        if peaks != "NOT FOUND" { spectrum.push_str(&peaks); }
        spectrum.push('\\n');"""

new_loop = """    for (i, spec) in data_list.iter().enumerate() {
        let comments = format!("FILENAME={}; FILEHASH={}; PREDICTED={}; SPLASH={}; SPECTRUMID={}; RESOLUTION={}; SYNON={}; FRAGMENTATIONMODE={}; AVERAGEMASS={}; ENTROPY={}; ONTOLOGIES = \\"CLASSYFIRE_SUPERCLASS={}, CLASSYFIRE_CLASS = {}, CLASSYFIRE_SUBCLASS = {}, NPCLASS_PATHWAY = {}, NPCLASS_SUPERCLASS = {}, NPCLASS_CLASS = {}\\"",
                               get_string(spec, "FILENAME"), get_string(spec, "FILEHASH"), get_string(spec, "PREDICTED"),
                               get_string(spec, "SPLASH"), get_string(spec, "SPECTRUMID"), get_string(spec, "RESOLUTION"),
                               get_string(spec, "SYNON"), get_string(spec, "FRAGMENTATIONMODE"), get_string(spec, "AVERAGEMASS"),
                               get_string(spec, "ENTROPY"), get_string(spec, "CLASSYFIRE_SUPERCLASS"), get_string(spec, "CLASSYFIRE_CLASS"),
                               get_string(spec, "CLASSYFIRE_SUBCLASS"), get_string(spec, "NPCLASS_PATHWAY"), get_string(spec, "NPCLASS_SUPERCLASS"),
                               get_string(spec, "NPCLASS_CLASS")
        );

        let mut spectrum = String::with_capacity(1024);
        spectrum.push_str("NAME: "); spectrum.push_str(&get_string(spec, "NAME")); spectrum.push('\\n');
        spectrum.push_str("PRECURSORMZ: "); spectrum.push_str(&get_string(spec, "PRECURSORMZ")); spectrum.push('\\n');
        spectrum.push_str("PRECURSORTYPE: "); spectrum.push_str(&get_string(spec, "PRECURSORTYPE")); spectrum.push('\\n');
        spectrum.push_str("FORMULA: "); spectrum.push_str(&get_string(spec, "FORMULA")); spectrum.push('\\n');
        spectrum.push_str("INCHIKEY: "); spectrum.push_str(&get_string(spec, "INCHIKEY")); spectrum.push('\\n');
        spectrum.push_str("INCHI: "); spectrum.push_str(&get_string(spec, "INCHI")); spectrum.push('\\n');
        spectrum.push_str("SMILES: "); spectrum.push_str(&get_string(spec, "SMILES")); spectrum.push('\\n');
        spectrum.push_str("RT: "); spectrum.push_str(&get_string(spec, "RT")); spectrum.push('\\n');
        spectrum.push_str("IONMODE: "); spectrum.push_str(&get_string(spec, "IONMODE")); spectrum.push('\\n');
        spectrum.push_str("INSTRUMENTTYPE: "); spectrum.push_str(&get_string(spec, "INSTRUMENTTYPE")); spectrum.push('\\n');
        spectrum.push_str("INSTRUMENT: "); spectrum.push_str(&get_string(spec, "INSTRUMENT")); spectrum.push('\\n');
        spectrum.push_str("COLLISIONENERGY: "); spectrum.push_str(&get_string(spec, "COLLISIONENERGY")); spectrum.push('\\n');
        spectrum.push_str("EXACTMASS: "); spectrum.push_str(&get_string(spec, "EXACTMASS")); spectrum.push('\\n');
        spectrum.push_str("IONIZATION: "); spectrum.push_str(&get_string(spec, "IONIZATION")); spectrum.push('\\n');
        spectrum.push_str("MSLEVEL: "); spectrum.push_str(&get_string(spec, "MSLEVEL")); spectrum.push('\\n');
        spectrum.push_str("COMMENT: "); spectrum.push_str(&comments); spectrum.push('\\n');
        spectrum.push_str("NUM PEAKS: "); spectrum.push_str(&get_string(spec, "NUM PEAKS")); spectrum.push('\\n');

        let peaks = get_string(spec, "PEAKS_LIST");
        if peaks != "NOT FOUND" { spectrum.push_str(&peaks); }
        spectrum.push('\\n');"""

content = content.replace(old_loop, new_loop)

content = content.replace("#[pyfunction]\n#[pyo3(signature = (pos_lc_df, pos_lc_df_insilico, pos_gc_df, pos_gc_df_insilico, neg_lc_df, neg_lc_df_insilico, neg_gc_df, neg_gc_df_insilico, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")

content = content.replace("pub fn csv_to_msp_processing<'py>(", "pub fn csv_to_msp_processing(")
content = content.replace("py: Python<'py>, pos_lc_df: Bound<'py, PyList>, pos_lc_df_insilico: Bound<'py, PyList>, pos_gc_df: Bound<'py, PyList>, pos_gc_df_insilico: Bound<'py, PyList>, neg_lc_df: Bound<'py, PyList>, neg_lc_df_insilico: Bound<'py, PyList>, neg_gc_df: Bound<'py, PyList>, neg_gc_df_insilico: Bound<'py, PyList>, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,",
                          "py: Python, pos_lc_df: Vec<Spectrum>, pos_lc_df_insilico: Vec<Spectrum>, pos_gc_df: Vec<Spectrum>, pos_gc_df_insilico: Vec<Spectrum>, neg_lc_df: Vec<Spectrum>, neg_lc_df_insilico: Vec<Spectrum>, neg_gc_df: Vec<Spectrum>, neg_gc_df_insilico: Vec<Spectrum>, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,")


with open('scripts/fraghub_rust/src/csv_to_msp.rs', 'w') as f:
    f.write(content)
