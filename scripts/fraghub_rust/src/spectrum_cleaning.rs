// src/spectrum_cleaning.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::path::Path;
use csv::WriterBuilder;

#[derive(Clone)]
struct RustSpectrum {
    index: usize,
    metadata: HashMap<String, String>,
    peaks: Vec<(f64, f64)>,
    is_empty_peaks: bool,
}

#[pyfunction]
#[pyo3(signature = (spectrum_list, output_directory, ordered_columns, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn spectrum_cleaning_processing<'py>(
    py: Python<'py>,
    spectrum_list: Bound<'py, PyList>,
    output_directory: String,
    ordered_columns: Vec<String>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyList>> {

    let total_items = spectrum_list.len();

    // ⚠️ ORDRE CRITIQUE POUR VUE.JS
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items,))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, ("cleaning spectrums:",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    // Importation des paramètres Python (backend_vars) sans modifier MAIN.py !
    let backend_vars = py.import_bound("scripts.backend_vars")?;
    let parameters_dict: HashMap<String, f64> = backend_vars.getattr("parameters_dict")?.extract()?;

    // ⚠️ LA PARTIE MANQUANTE : LE CONTEXTE JSON ⚠️
    let globals = py.import_bound("scripts.globals_vars")?;
    let json_module = py.import_bound("json")?;

    let adduct_pos_str: String = json_module.call_method1("dumps", (globals.getattr("adduct_dict_POS")?,))?.extract()?;
    let adduct_neg_str: String = json_module.call_method1("dumps", (globals.getattr("adduct_dict_NEG")?,))?.extract()?;
    let mass_pos_str: String = json_module.call_method1("dumps", (globals.getattr("adduct_massdiff_dict_POS")?,))?.extract()?;
    let mass_neg_str: String = json_module.call_method1("dumps", (globals.getattr("adduct_massdiff_dict_NEG")?,))?.extract()?;
    let tree_str: String = json_module.call_method1("dumps", (globals.getattr("instrument_tree")?,))?.extract()?;

    let context = crate::normalizer::NormalizerContext {
        adduct_pos: serde_json::from_str(&adduct_pos_str).unwrap(),
        adduct_neg: serde_json::from_str(&adduct_neg_str).unwrap(),
        adduct_massdiff_pos: serde_json::from_str(&mass_pos_str).unwrap(),
        adduct_massdiff_neg: serde_json::from_str(&mass_neg_str).unwrap(),
        instrument_tree: serde_json::from_str(&tree_str).unwrap(),
    };

    // 1. Extraction ultra-rapide des données vers Rust
    let mut rust_spectra = Vec::with_capacity(total_items);
    for (i, item) in spectrum_list.iter().enumerate() {
        let dict = item.downcast::<PyDict>()?;
        let mut metadata = HashMap::new();
        let mut peaks = Vec::new();
        let mut is_empty_peaks = true;

        for (k, v) in dict.iter() {
            let key_str = k.extract::<String>()?;
            if key_str == "PEAKS_LIST" {
                if let Ok(extracted_peaks) = v.extract::<Vec<Vec<f64>>>() {
                    peaks = extracted_peaks.into_iter().filter_map(|p| {
                        if p.len() >= 2 { Some((p[0], p[1])) } else { None }
                    }).collect();
                    if !peaks.is_empty() { is_empty_peaks = false; }
                } else if let Ok(s) = v.extract::<String>() {
                    if !s.trim().is_empty() {
                        for line in s.split('\n') {
                            let parts: Vec<&str> = line.split_whitespace().collect();
                            if parts.len() >= 2 {
                                if let (Ok(mz), Ok(int)) = (parts[0].parse::<f64>(), parts[1].parse::<f64>()) {
                                    peaks.push((mz, int));
                                }
                            }
                        }
                        if !peaks.is_empty() { is_empty_peaks = false; }
                    }
                }
            } else {
                let val_str = if let Ok(s) = v.extract::<String>() { s } else { v.to_string() };
                metadata.insert(key_str, val_str);
            }
        }
        rust_spectra.push(RustSpectrum { index: i, metadata, peaks, is_empty_peaks });
    }

    // 2. Traitement Multithreadé (Rayon)
    let chunk_size = 2000;
    let mut processed = 0;
    let mut kept_spectra = Vec::new();
    let mut deleted_spectra: HashMap<String, Vec<HashMap<String, String>>> = HashMap::new();

    for chunk in rust_spectra.chunks(chunk_size) {
        let results: Vec<_> = chunk.par_iter().map(|spec| {
            let mut meta = spec.metadata.clone();

            if spec.is_empty_peaks {
                return Err((meta, "spectrum deleted because peaks list is empty".to_string()));
            }

            let mut deletion_reason = None;
            // Appel du Normalizer AVEC le contexte
            let metadata_opt = crate::normalizer::values_normalizer::normalize_values(meta.clone(), &mut deletion_reason, &context);

            if let Some(mut valid_meta) = metadata_opt {
                let filename = valid_meta.get("FILENAME").cloned().unwrap_or_default();
                let instrument = valid_meta.get("INSTRUMENTTYPE").cloned().unwrap_or_default();
                let is_gc = filename.contains("_GC") || crate::globals_vars::GC_PATTERN.is_match(&instrument);

                let mut float_pmz: Option<f64> = None;

                if !is_gc {
                    if let Some(pmz) = valid_meta.get("PRECURSORMZ") {
                        if let Some(caps) = crate::globals_vars::FLOAT_CHECK_PATTERN.captures(pmz) {
                            let matched_str = caps.get(1).unwrap().as_str();
                            let replaced = matched_str.replace(',', ".");
                            if let Ok(val) = replaced.parse::<f64>() {
                                if val <= 0.0 { return Err((valid_meta, "spectrum deleted because precursor mz is less than or equal to zero.".to_string())); }
                                valid_meta.insert("PRECURSORMZ".to_string(), matched_str.to_string());
                                float_pmz = Some(val);
                            } else { return Err((valid_meta, "spectrum deleted because precursor mz field is empty or contains invalid characters (not a floating number).".to_string())); }
                        } else { return Err((valid_meta, "spectrum deleted because precursor mz field is empty or contains invalid characters (not a floating number).".to_string())); }
                    } else { return Err((valid_meta, "spectrum deleted because precursor mz field is empty or contains invalid characters (not a floating number).".to_string())); }
                }

                // Filtrage des pics
                let mut peaks = spec.peaks.clone();
                peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));

                let mut peak_del_reason = None;
                peaks = crate::peaks_filters::filters::apply_filters(peaks, float_pmz, &parameters_dict, &mut peak_del_reason);

                if peaks.is_empty() {
                    let reason = peak_del_reason.unwrap_or_else(|| "spectrum deleted because peaks list is empty".to_string());
                    return Err((valid_meta, reason));
                }

                // Calcul de l'entropie
                let intensities: Vec<f64> = peaks.iter().map(|p| p.1).collect();
                let entropy = crate::peaks_filters::entropy_calculation::entropy_calculation(&intensities);
                valid_meta.insert("ENTROPY".to_string(), format!("{:.8}", entropy));

                if *parameters_dict.get("remove_spectrum_under_entropy_score").unwrap_or(&0.0) == 1.0 {
                    let threshold = *parameters_dict.get("remove_spectrum_under_entropy_score_value").unwrap_or(&0.0);
                    if entropy < threshold {
                        return Err((valid_meta, "spectrum deleted because it's entropy score is lower than the threshold selected by the user.".to_string()));
                    }
                }

                valid_meta.insert("NUM PEAKS".to_string(), peaks.len().to_string());

                let mut formatted_peaks = String::new();
                for (i, &(mz, int)) in peaks.iter().enumerate() {
                    if i > 0 { formatted_peaks.push('\n'); }
                    formatted_peaks.push_str(&format!("{:.8} {:.8}", mz, int));
                }
                valid_meta.insert("PEAKS_LIST".to_string(), formatted_peaks);

                Ok(valid_meta)
            } else {
                Err((meta, deletion_reason.unwrap_or_else(|| "Unknown deletion reason".to_string())))
            }
        }).collect();

        // Répartition des succès et des erreurs
        for res in results {
            match res {
                Ok(meta) => kept_spectra.push(meta),
                Err((mut meta, reason)) => {
                    meta.insert("DELETION_REASON".to_string(), reason.clone());
                    deleted_spectra.entry(reason).or_default().push(meta);
                }
            }
        }

        processed += chunk.len();
        if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
    }

    // 3. Mise à jour de deletion_report.py EN DIRECT !
    let del_report = py.import_bound("scripts.deletion_report")?;
    for (reason, group) in &deleted_spectra {
        let count = group.len() as i32;
        let py_var = match reason.as_str() {
            "spectrum deleted because peaks list is empty" => "no_peaks_list",
            "spectrum deleted because precursor mz is less than or equal to zero." => "no_precursor_mz",
            "spectrum deleted because precursor mz field is empty or contains invalid characters (not a floating number)." => "no_precursor_mz",
            "spectrum deleted because it's entropy score is lower than the threshold selected by the user." => "low_entropy_score",
            "spectrum deleted because it has neither inchi nor smiles nor inchikey" => "no_smiles_no_inchi_no_inchikey",
            "spectrum deleted because its adduct field is empty or the value entered is not an adduct" => "no_or_bad_adduct",
            "spectrum deleted because the adduct corresponds to the wrong ionization mode (neg adduct in pos ionmode)." => "no_or_bad_adduct",
            "spectrum deleted because the adduct corresponds to the wrong ionization mode (pos adduct in neg ionmode)." => "no_or_bad_adduct",
            "spectrum deleted because its number of peaks is below the threshold chosen by the user" => "minimum_peaks_not_requiered",
            "spectrum deleted because peaks list is empty after removing peaks above precursor m/z" => "all_peaks_above_precursor_mz",
            "spectrum deleted because peaks list is empty after removing peaks out of mz range choiced by the user" => "no_peaks_in_mz_range",
            "spectrum deleted because peaks list does not contain minimum number of high peaks required according to the value choiced by the user" => "minimum_high_peaks_not_requiered",
            _ => continue,
        };
        let current: i32 = del_report.getattr(py_var)?.extract()?;
        del_report.setattr(py_var, current + count)?;
    }

    // 4. Écriture des CSV de suppression
    if !deleted_spectra.is_empty() {
        let del_dir = Path::new(&output_directory).join("DELETED_SPECTRUMS");
        fs::create_dir_all(&del_dir)?;

        for (reason, group) in deleted_spectra {
            let file_name = match reason.as_str() {
                "spectrum deleted because peaks list is empty" => "peaks_list_is_empty.csv",
                "spectrum deleted because precursor mz is less than or equal to zero." => "precursor_mz_less_than_or_equal_zero.csv",
                "spectrum deleted because it's entropy score is lower than the threshold selected by the user." => "entropy_score_lower_than_threshold.csv",
                "spectrum deleted because precursor mz field is empty or contains invalid characters (not a floating number)." => "precursor_mz_invalid_or_empty.csv",
                "spectrum deleted because it has neither inchi nor smiles nor inchikey" => "no_inchi_smiles_or_inchikey.csv",
                "spectrum deleted because its adduct field is empty or the value entered is not an adduct" => "adduct_empty_or_invalid.csv",
                "spectrum deleted because the adduct corresponds to the wrong ionization mode (neg adduct in pos ionmode)." => "wrong_adduct_neg_in_pos.csv",
                "spectrum deleted because the adduct corresponds to the wrong ionization mode (pos adduct in neg ionmode)." => "wrong_adduct_pos_in_neg.csv",
                "spectrum deleted because its number of peaks is below the threshold chosen by the user" => "number_of_peaks_below_threshold.csv",
                "spectrum deleted because peaks list is empty after removing peaks above precursor m/z" => "peaks_empty_after_above_precursor_mz_removal.csv",
                "spectrum deleted because peaks list is empty after removing peaks out of mz range choiced by the user" => "peaks_empty_after_mz_range_removal.csv",
                "spectrum deleted because peaks list does not contain minimum number of high peaks required according to the value choiced by the user" => "insufficient_high_peaks.csv",
                _ => "other_deletions.csv"
            };

            let mut wtr = WriterBuilder::new().delimiter(b'\t').quote(b'"').from_path(del_dir.join(file_name)).unwrap();
            let mut header = ordered_columns.clone();
            header.push("DELETION_REASON".to_string());
            wtr.write_record(&header).unwrap();

            for meta in group {
                let mut record = Vec::with_capacity(ordered_columns.len() + 1);
                for col in &ordered_columns {
                    record.push(meta.get(col).cloned().unwrap_or_default());
                }
                record.push(meta.get("DELETION_REASON").cloned().unwrap_or_default());
                wtr.write_record(&record).unwrap();
            }
            wtr.flush().unwrap();
        }
    }

    // 5. Reconstruction de la liste finale
    let py_final_list = PyList::empty_bound(py);
    for meta in kept_spectra {
        let py_dict = PyDict::new_bound(py);
        for (k, v) in meta { py_dict.set_item(k, v)?; }
        py_final_list.append(py_dict)?;
    }

    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    Ok(py_final_list)
}