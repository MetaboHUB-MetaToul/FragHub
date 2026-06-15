// src/report.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyAny, PyList};
use std::fs::File;
use std::io::Write;
use std::path::Path;

// Fonction utilitaire pour extraire la taille et les INCHIKEYs uniques d'un DataFrame via PyO3

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
}


#[pyfunction]
#[pyo3(signature = (output_directory, date_str, parameters_dict, deletion_dict, pos_lc, pos_lc_insilico, pos_gc, pos_gc_insilico, neg_lc, neg_lc_insilico, neg_gc, neg_gc_insilico))]
pub fn generate_report_processing<'py>(
    py: Python<'py>,
    output_directory: String,
    date_str: String,
    parameters_dict: &Bound<'py, PyDict>,
    deletion_dict: &Bound<'py, PyDict>,
    pos_lc: &Bound<'py, PyAny>,
    pos_lc_insilico: &Bound<'py, PyAny>,
    pos_gc: &Bound<'py, PyAny>,
    pos_gc_insilico: &Bound<'py, PyAny>,
    neg_lc: &Bound<'py, PyAny>,
    neg_lc_insilico: &Bound<'py, PyAny>,
    neg_gc: &Bound<'py, PyAny>,
    neg_gc_insilico: &Bound<'py, PyAny>,
) -> PyResult<()> {

    // 1. Extraction des statistiques des 8 DataFrames
    let (pos_lc_len, pos_lc_uniq) = get_df_stats(pos_lc)?;
    let (pos_lc_in_len, pos_lc_in_uniq) = get_df_stats(pos_lc_insilico)?;
    let (pos_gc_len, pos_gc_uniq) = get_df_stats(pos_gc)?;
    let (pos_gc_in_len, pos_gc_in_uniq) = get_df_stats(pos_gc_insilico)?;
    let (neg_lc_len, neg_lc_uniq) = get_df_stats(neg_lc)?;
    let (neg_lc_in_len, neg_lc_in_uniq) = get_df_stats(neg_lc_insilico)?;
    let (neg_gc_len, neg_gc_uniq) = get_df_stats(neg_gc)?;
    let (neg_gc_in_len, neg_gc_in_uniq) = get_df_stats(neg_gc_insilico)?;

    let total_spectra = pos_lc_len + pos_lc_in_len + pos_gc_len + pos_gc_in_len + neg_lc_len + neg_lc_in_len + neg_gc_len + neg_gc_in_len;
    let total_unique = pos_lc_uniq + pos_lc_in_uniq + pos_gc_uniq + pos_gc_in_uniq + neg_lc_uniq + neg_lc_in_uniq + neg_gc_uniq + neg_gc_in_uniq;

    // 2. Formatage des chaînes (Equivalent exact de votre Python)

    // Helper pour récupérer des booléens ou strings du dict Python
    let get_bool = |key: &str| -> bool {
        parameters_dict.get_item(key).ok().flatten().and_then(|v| v.extract::<f64>().ok()).unwrap_or(0.0) == 1.0
    };
    let get_f64 = |key: &str| -> f64 {
        parameters_dict.get_item(key).ok().flatten().and_then(|v| v.extract::<f64>().ok()).unwrap_or(0.0)
    };
    let get_del = |key: &str| -> i64 {
        deletion_dict.get_item(key).ok().flatten().and_then(|v| v.extract::<i64>().ok()).unwrap_or(0)
    };

    // Fichiers d'entrée (Extraction depuis la liste Python)
    let mut msp_files = String::new();
    let mut json_files = String::new();
    let mut csv_files = String::new();
    let mut mgf_files = String::new();

    if let Ok(Some(input_dir)) = parameters_dict.get_item("input_directory") {
        if let Ok(list) = input_dir.downcast::<PyList>() {
            for item in list {
                if let Ok(file_str) = item.extract::<String>() {
                    let formatted = format!("\t\t\t{}\n", file_str);
                    if file_str.ends_with(".msp") { msp_files.push_str(&formatted); }
                    else if file_str.ends_with(".json") { json_files.push_str(&formatted); }
                    else if file_str.ends_with(".csv") { csv_files.push_str(&formatted); }
                    else if file_str.ends_with(".mgf") { mgf_files.push_str(&formatted); }
                }
            }
        }
    }

    if msp_files.is_empty() { msp_files = "\t\t\t-- no file --\n".to_string(); }
    if json_files.is_empty() { json_files = "\t\t\t-- no file --\n".to_string(); }
    if csv_files.is_empty() { csv_files = "\t\t\t-- no file --\n".to_string(); }
    if mgf_files.is_empty() { mgf_files = "\t\t\t-- no file --\n".to_string(); }

    let report_content = format!(
        r#"
======================= FILES =======================
INPUT_FILES:
    MSP:
{}    JSON:
{}    CSV:
{}    MGF:
{}
OUTPUT_DIRECTORY:
    {}

OUTPUT_FORMAT:
    CSV: {}
    MSP: {}
    jSON: {}

===================== PARAMETERS =====================
normalize_intensity: {}
remove_peak_above_precursormz: {}
check_minimum_peak_requiered: {}
    n_peaks: {}
reduce_peak_list: {}
    max_peaks: {}
remove_spectrum_under_entropy_score: {}
    entropy_score_value: {}
keep_mz_in_range: {}
    from_mz: {}
    to_mz: {}
check_minimum_of_high_peaks_requiered: {}
    intensity_percent: {}
    no_peaks: {}

reset_updates: {}

======================= FILTERED OUT =======================
No peaks list: {}
No smiles, no inchi, no inchikey: {}
No precursor mz: {}
No or bad adduct: {}
Low entropy score: {}
Minimum peaks not required: {}
All peaks above precursor mz: {}
No peaks in mz range: {}
Minimum high peaks not required: {}
Duplicatas removed: {}

================== SPECTRUM NUMBER ==================
POS LC Exp: {}
NEG LC Exp: {}
POS LC InSilico: {}
NEG LC InSilico: {}
POS GC Exp: {}
NEG GC Exp: {}
POS GC InSilico: {}
NEG GC InSilico: {}

Total: {}

================= UNIQUE INCHIKEYS ==================
POS LC Exp: {}
NEG LC Exp: {}
POS LC InSilico: {}
NEG LC InSilico: {}
POS GC Exp: {}
NEG GC Exp: {}
POS GC InSilico: {}
NEG GC InSilico: {}

TOTAL Unique InChIKeys: {}
"#,
        msp_files, json_files, csv_files, mgf_files,
        output_directory,
        if get_bool("csv") { "YES" } else { "NO" },
        if get_bool("msp") { "YES" } else { "NO" },
        if get_bool("json") { "YES" } else { "NO" },
        if get_bool("normalize_intensity") { "ON" } else { "OFF" },
        if get_bool("remove_peak_above_precursormz") { "ON" } else { "OFF" },
        if get_bool("check_minimum_peak_requiered") { "ON" } else { "OFF" },
        get_f64("check_minimum_peak_requiered_n_peaks"),
        if get_bool("reduce_peak_list") { "ON" } else { "OFF" },
        get_f64("reduce_peak_list_max_peaks"),
        if get_bool("remove_spectrum_under_entropy_score") { "ON" } else { "OFF" },
        get_f64("remove_spectrum_under_entropy_score_value"),
        if get_bool("keep_mz_in_range") { "ON" } else { "OFF" },
        get_f64("keep_mz_in_range_from_mz"),
        get_f64("keep_mz_in_range_to_mz"),
        if get_bool("check_minimum_of_high_peaks_requiered") { "ON" } else { "OFF" },
        get_f64("check_minimum_of_high_peaks_requiered_intensity_percent"),
        get_f64("check_minimum_of_high_peaks_requiered_no_peaks"),
        if get_bool("reset_updates") { "YES" } else { "NO" },

        get_del("no_peaks_list"),
        get_del("no_smiles_no_inchi_no_inchikey"),
        get_del("no_precursor_mz"),
        get_del("no_or_bad_adduct"),
        get_del("low_entropy_score"),
        get_del("minimum_peaks_not_requiered"),
        get_del("all_peaks_above_precursor_mz"),
        get_del("no_peaks_in_mz_range"),
        get_del("minimum_high_peaks_not_requiered"),
        get_del("duplicatas_removed"),

        pos_lc_len, neg_lc_len, pos_lc_in_len, neg_lc_in_len, pos_gc_len, neg_gc_len, pos_gc_in_len, neg_gc_in_len, total_spectra,
        pos_lc_uniq, neg_lc_uniq, pos_lc_in_uniq, neg_lc_in_uniq, pos_gc_uniq, neg_gc_uniq, pos_gc_in_uniq, neg_gc_in_uniq, total_unique
    );

    // 3. Écriture du fichier
    let file_name = format!("report_{}.txt", date_str);
    let report_path = Path::new(&output_directory).join(file_name);

    let mut file = File::create(report_path)?;
    file.write_all(report_content.as_bytes())?;

    Ok(())
}