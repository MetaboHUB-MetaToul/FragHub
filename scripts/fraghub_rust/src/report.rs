// src/report.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;
use std::fs::File;
use std::io::Write;
use std::path::Path;

// Fonction utilitaire pour extraire la taille et les INCHIKEYs uniques d'un Vec<Spectrum>

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
}


/// Génère le rapport final (report.txt) récapitulant les paramètres et le résultat du nettoyage.
///
/// Pour un développeur Python : Ce fichier contient le formatage d'une très longue chaîne.
/// En Rust, on utilise `format!(r#"..."#)` pour manipuler du texte brut multi-lignes ("raw strings") 
/// sans avoir besoin d'échapper les guillemets ou caractères spéciaux.
pub fn generate_report_processing(
    _py: Python,
    output_directory: String,
    date_str: String,
    parameters_dict: &std::collections::HashMap<String, f64>,
    input_paths: &Vec<String>,
    deletion_report: &crate::deletion_report::DeletionReport,
    pos_lc: &Vec<Spectrum>,
    pos_lc_insilico: &Vec<Spectrum>,
    pos_gc: &Vec<Spectrum>,
    pos_gc_insilico: &Vec<Spectrum>,
    neg_lc: &Vec<Spectrum>,
    neg_lc_insilico: &Vec<Spectrum>,
    neg_gc: &Vec<Spectrum>,
    neg_gc_insilico: &Vec<Spectrum>,
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

    // Helpers natifs
    let get_bool = |key: &str| -> bool {
        parameters_dict.get(key).cloned().unwrap_or(0.0) == 1.0
    };
    let get_f64 = |key: &str| -> f64 {
        parameters_dict.get(key).cloned().unwrap_or(0.0)
    };

    
    
    let mut msp_files = String::new();
    let mut json_files = String::new();
    let mut csv_files = String::new();
    let mut mgf_files = String::new();

    for file_str in input_paths {
        let formatted = format!("<li>{}</li>", file_str);
        if file_str.ends_with(".msp") { msp_files.push_str(&formatted); }
        else if file_str.ends_with(".json") { json_files.push_str(&formatted); }
        else if file_str.ends_with(".csv") { csv_files.push_str(&formatted); }
        else if file_str.ends_with(".mgf") { mgf_files.push_str(&formatted); }
    }

    if msp_files.is_empty() { msp_files = "<li>-- no file --</li>".to_string(); }
    if json_files.is_empty() { json_files = "<li>-- no file --</li>".to_string(); }
    if csv_files.is_empty() { csv_files = "<li>-- no file --</li>".to_string(); }
    if mgf_files.is_empty() { mgf_files = "<li>-- no file --</li>".to_string(); }

    let get_bool_str = |key: &str| -> &str { if get_bool(key) { "ON" } else { "OFF" } };
    let get_class_str = |key: &str| -> &str { if get_bool(key) { "on" } else { "off" } };

    let total_deletions = deletion_report.duplicatas_removed +
        deletion_report.previously_cleaned +
        deletion_report.no_peaks_list +
        deletion_report.no_smiles_no_inchi_no_inchikey +
        deletion_report.no_precursor_mz +
        deletion_report.no_or_bad_adduct +
        deletion_report.low_entropy_score +
        deletion_report.minimum_peaks_not_requiered +
        deletion_report.all_peaks_above_precursor_mz +
        deletion_report.no_peaks_in_mz_range +
        deletion_report.minimum_high_peaks_not_requiered;

    let total_input = total_spectra + total_deletions;
    let max_h = if total_input > 0 { total_input as f64 } else { 1.0 };
    let pct_del = (total_deletions as f64 / max_h) * 100.0;
    let pct_out = (total_spectra as f64 / max_h) * 100.0;

    let calc_h = |val: usize| {
        if total_deletions > 0 { (val as f64 / total_deletions as f64) * 100.0 } else { 0.0 }
    };

    let mut html = String::from(include_str!("report_template.html"));

    html = html.replace("{DATE}", &date_str.replace("_", " ").replace("  ", " at "));
    html = html.replace("{MSP}", &msp_files);
    html = html.replace("{JSON}", &json_files);
    html = html.replace("{CSV}", &csv_files);
    html = html.replace("{MGF}", &mgf_files);
    html = html.replace("{OUT_DIR}", &output_directory);
    html = html.replace("{OUT_CSV}", if get_bool("csv") { "YES" } else { "NO" });
    html = html.replace("{OUT_MSP}", if get_bool("msp") { "YES" } else { "NO" });
    html = html.replace("{OUT_JSON}", if get_bool("json") { "YES" } else { "NO" });

    html = html.replace("{V1}", get_bool_str("normalize_intensity")).replace("{C1}", get_class_str("normalize_intensity"));
    html = html.replace("{V2}", get_bool_str("remove_peak_above_precursormz")).replace("{C2}", get_class_str("remove_peak_above_precursormz"));
    html = html.replace("{V3}", get_bool_str("check_minimum_peak_requiered")).replace("{C3}", get_class_str("check_minimum_peak_requiered"));
    html = html.replace("{V3_1}", &get_f64("check_minimum_peak_requiered_n_peaks").to_string());
    html = html.replace("{V4}", get_bool_str("reduce_peak_list")).replace("{C4}", get_class_str("reduce_peak_list"));
    html = html.replace("{V4_1}", &get_f64("reduce_peak_list_max_peaks").to_string());
    html = html.replace("{V5}", get_bool_str("remove_spectrum_under_entropy_score")).replace("{C5}", get_class_str("remove_spectrum_under_entropy_score"));
    html = html.replace("{V5_1}", &get_f64("remove_spectrum_under_entropy_score_value").to_string());
    html = html.replace("{V6}", get_bool_str("keep_mz_in_range")).replace("{C6}", get_class_str("keep_mz_in_range"));
    html = html.replace("{V6_1}", &get_f64("keep_mz_in_range_from_mz").to_string()).replace("{V6_2}", &get_f64("keep_mz_in_range_to_mz").to_string());
    html = html.replace("{V7}", get_bool_str("check_minimum_of_high_peaks_requiered")).replace("{C7}", get_class_str("check_minimum_of_high_peaks_requiered"));
    html = html.replace("{V7_1}", &get_f64("check_minimum_of_high_peaks_requiered_intensity_percent").to_string());
    html = html.replace("{V7_2}", &get_f64("check_minimum_of_high_peaks_requiered_no_peaks").to_string());
    html = html.replace("{V8}", get_bool_str("reset_updates")).replace("{C8}", get_class_str("reset_updates"));

    html = html.replace("{TOTAL_IN}", &total_input.to_string());
    html = html.replace("{TOTAL_DEL}", &total_deletions.to_string());
    html = html.replace("{TOTAL_OUT}", &total_spectra.to_string());
    html = html.replace("{TOTAL_UNIQ}", &total_unique.to_string());
    
    html = html.replace("{PCT_DEL}", &pct_del.to_string());
    html = html.replace("{PCT_OUT}", &pct_out.to_string());

    html = html.replace("{H_PEAKS}", &calc_h(deletion_report.no_peaks_list).to_string());
    html = html.replace("{V_PEAKS}", &deletion_report.no_peaks_list.to_string());
    html = html.replace("{H_SMILES}", &calc_h(deletion_report.no_smiles_no_inchi_no_inchikey).to_string());
    html = html.replace("{V_SMILES}", &deletion_report.no_smiles_no_inchi_no_inchikey.to_string());
    html = html.replace("{H_PRECURSOR}", &calc_h(deletion_report.no_precursor_mz).to_string());
    html = html.replace("{V_PRECURSOR}", &deletion_report.no_precursor_mz.to_string());
    html = html.replace("{H_ADDUCT}", &calc_h(deletion_report.no_or_bad_adduct).to_string());
    html = html.replace("{V_ADDUCT}", &deletion_report.no_or_bad_adduct.to_string());
    html = html.replace("{H_ENTROPY}", &calc_h(deletion_report.low_entropy_score).to_string());
    html = html.replace("{V_ENTROPY}", &deletion_report.low_entropy_score.to_string());
    html = html.replace("{H_MIN_PEAKS}", &calc_h(deletion_report.minimum_peaks_not_requiered).to_string());
    html = html.replace("{V_MIN_PEAKS}", &deletion_report.minimum_peaks_not_requiered.to_string());
    html = html.replace("{H_ABOVE_PREC}", &calc_h(deletion_report.all_peaks_above_precursor_mz).to_string());
    html = html.replace("{V_ABOVE_PREC}", &deletion_report.all_peaks_above_precursor_mz.to_string());
    html = html.replace("{H_RANGE}", &calc_h(deletion_report.no_peaks_in_mz_range).to_string());
    html = html.replace("{V_RANGE}", &deletion_report.no_peaks_in_mz_range.to_string());
    html = html.replace("{H_HIGH_PEAKS}", &calc_h(deletion_report.minimum_high_peaks_not_requiered).to_string());
    html = html.replace("{V_HIGH_PEAKS}", &deletion_report.minimum_high_peaks_not_requiered.to_string());
    html = html.replace("{H_DUP}", &calc_h(deletion_report.duplicatas_removed).to_string());
    html = html.replace("{V_DUP}", &deletion_report.duplicatas_removed.to_string());
    html = html.replace("{H_PREV}", &calc_h(deletion_report.previously_cleaned).to_string());
    html = html.replace("{V_PREV}", &deletion_report.previously_cleaned.to_string());


    let lc_pos_tot = pos_lc_len + pos_lc_in_len;
    let lc_neg_tot = neg_lc_len + neg_lc_in_len;
    let gc_pos_tot = pos_gc_len + pos_gc_in_len;
    let gc_neg_tot = neg_gc_len + neg_gc_in_len;
    let lc_tot = lc_pos_tot + lc_neg_tot;
    let gc_tot = gc_pos_tot + gc_neg_tot;

    let lc_pos_uniq = pos_lc_uniq + pos_lc_in_uniq;
    let lc_neg_uniq = neg_lc_uniq + neg_lc_in_uniq;
    let gc_pos_uniq = pos_gc_uniq + pos_gc_in_uniq;
    let gc_neg_uniq = neg_gc_uniq + neg_gc_in_uniq;
    let lc_uniq = lc_pos_uniq + lc_neg_uniq;
    let gc_uniq = gc_pos_uniq + gc_neg_uniq;

    html = html.replace("{LC_TOT}", &lc_tot.to_string());
    html = html.replace("{GC_TOT}", &gc_tot.to_string());
    html = html.replace("{LC_POS_TOT}", &lc_pos_tot.to_string());
    html = html.replace("{LC_NEG_TOT}", &lc_neg_tot.to_string());
    html = html.replace("{GC_POS_TOT}", &gc_pos_tot.to_string());
    html = html.replace("{GC_NEG_TOT}", &gc_neg_tot.to_string());

    html = html.replace("{LC_UNIQ}", &lc_uniq.to_string());
    html = html.replace("{GC_UNIQ}", &gc_uniq.to_string());
    html = html.replace("{LC_POS_UNIQ}", &lc_pos_uniq.to_string());
    html = html.replace("{LC_NEG_UNIQ}", &lc_neg_uniq.to_string());
    html = html.replace("{GC_POS_UNIQ}", &gc_pos_uniq.to_string());
    html = html.replace("{GC_NEG_UNIQ}", &gc_neg_uniq.to_string());

    html = html.replace("{T1}", &pos_lc_len.to_string()); html = html.replace("{U1}", &pos_lc_uniq.to_string());
    html = html.replace("{T2}", &neg_lc_len.to_string()); html = html.replace("{U2}", &neg_lc_uniq.to_string());
    html = html.replace("{T3}", &pos_lc_in_len.to_string()); html = html.replace("{U3}", &pos_lc_in_uniq.to_string());
    html = html.replace("{T4}", &neg_lc_in_len.to_string()); html = html.replace("{U4}", &neg_lc_in_uniq.to_string());
    html = html.replace("{T5}", &pos_gc_len.to_string()); html = html.replace("{U5}", &pos_gc_uniq.to_string());
    html = html.replace("{T6}", &neg_gc_len.to_string()); html = html.replace("{U6}", &neg_gc_uniq.to_string());
    html = html.replace("{T7}", &pos_gc_in_len.to_string()); html = html.replace("{U7}", &pos_gc_in_uniq.to_string());
    html = html.replace("{T8}", &neg_gc_in_len.to_string()); html = html.replace("{U8}", &neg_gc_in_uniq.to_string());

    let file_name = format!("report_{}.html", date_str);
    let report_path = Path::new(&output_directory).join(file_name);
    let mut file = File::create(report_path)?;
    file.write_all(html.as_bytes())?;
    
    Ok(())
}
