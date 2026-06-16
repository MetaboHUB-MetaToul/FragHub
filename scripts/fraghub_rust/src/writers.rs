// src/writers.rs
use pyo3::prelude::*;
use crate::spectrum::Spectrum;
use std::fs::{self, OpenOptions};
use std::io::{Write, Seek, SeekFrom, Read};
use std::path::Path;
use csv::WriterBuilder;
use once_cell::sync::Lazy;
use regex::Regex;

fn write_msp(
    py: Python, spectrum_list: &Vec<String>, filename: &str, mode: &str, update: bool, output_directory: &str,
    progress_callback: &Option<PyObject>, total_items_callback: &Option<PyObject>, prefix_callback: &Option<PyObject>, item_type_callback: &Option<PyObject>,
) -> PyResult<()> {
    let len = spectrum_list.len();
    if len == 0 { return Ok(()); }

    let path_dir = Path::new(output_directory).join("MSP").join(mode);
    fs::create_dir_all(&path_dir)?;
    let file_path = path_dir.join(filename);

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Writing {} to MSP:", filename),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("spectra",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    let mut file = OpenOptions::new().write(true).create(true).append(update).truncate(!update).open(&file_path)?;

    for (i, spec_str) in spectrum_list.iter().enumerate() {
        file.write_all(spec_str.as_bytes())?;
        file.write_all(b"\n\n")?;
        
        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    file.flush()?;
    Ok(())
}

fn write_csv(
    py: Python, data_list: &Vec<Spectrum>, ordered_columns: &Vec<String>, filename: &str, mode: &str, update: bool, output_directory: &str,
    progress_callback: &Option<PyObject>, total_items_callback: &Option<PyObject>, prefix_callback: &Option<PyObject>, item_type_callback: &Option<PyObject>,
) -> PyResult<()> {
    let len = data_list.len();
    if len == 0 { return Ok(()); }

    let path_dir = Path::new(output_directory).join("CSV").join(mode);
    fs::create_dir_all(&path_dir)?;
    let file_path = path_dir.join(filename);

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Writing {} to CSV:", filename),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("rows",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    let is_append = update && file_path.exists();
    let file = OpenOptions::new().write(true).create(true).append(is_append).truncate(!is_append).open(&file_path)?;
    let mut wtr = WriterBuilder::new().delimiter(b'\t').quote(b'"').has_headers(!is_append).from_writer(file);

    if !is_append {
        wtr.write_record(ordered_columns).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
    }

    for (i, spec) in data_list.iter().enumerate() {
        let mut row = Vec::with_capacity(ordered_columns.len());

        for col in ordered_columns {
            let mut cell_val = String::new();
            
            if col == "PEAKS_LIST" {
                if !spec.peaks.is_empty() {
                    let mut peaks_str = String::with_capacity(spec.peaks.len() * 20);
                    for (i, &(mz, int)) in spec.peaks.iter().enumerate() {
                        if i > 0 { peaks_str.push(';'); }
                        peaks_str.push_str(&format!("{} {}", mz, int));
                    }
                    cell_val = peaks_str;
                }
            } else if let Some(val) = spec.metadata.get(col) {
                if !val.eq_ignore_ascii_case("nan") {
                    cell_val = val.clone();
                }
            }
            row.push(cell_val);
        }
        wtr.write_record(&row).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    wtr.flush()?;
    Ok(())
}

fn write_json(
    py: Python, update: bool, data_list: &Vec<Spectrum>, filename: &str, mode: &str, output_directory: &str,
    progress_callback: &Option<PyObject>, total_items_callback: &Option<PyObject>, prefix_callback: &Option<PyObject>, item_type_callback: &Option<PyObject>,
) -> PyResult<()> {
    let len = data_list.len();
    if len == 0 { return Ok(()); }

    let path_dir = Path::new(output_directory).join("JSON").join(mode);
    fs::create_dir_all(&path_dir)?;
    let file_path = path_dir.join(filename);

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Writing {} to JSON:", filename),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("rows",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    let is_append_mode = update && file_path.exists() && fs::metadata(&file_path).map(|m| m.len()).unwrap_or(0) > 2;
    let mut file = if is_append_mode {
        let mut f = OpenOptions::new().read(true).write(true).open(&file_path)?;
        let file_len = f.metadata()?.len();
        if file_len > 0 {
            let mut buf = [0u8; 1];
            for offset in 1..=std::cmp::min(10, file_len) {
                f.seek(SeekFrom::End(-(offset as i64)))?;
                f.read_exact(&mut buf)?;
                if buf[0] == b']' {
                    f.set_len(file_len - offset)?;
                    f.seek(SeekFrom::End(0))?;
                    f.write_all(b",\n")?;
                    break;
                }
            }
        }
        f
    } else {
        let mut f = OpenOptions::new().write(true).create(true).truncate(true).open(&file_path)?;
        f.write_all(b"[\n")?;
        f
    };

    // Récupération dynamique des clés du premier dictionnaire pour le JSON
    let first_spec = &data_list[0];
    let columns: Vec<String> = first_spec.metadata.keys().cloned().collect();

    static RE_3: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\n\s*(-?[\d\.eE\+\-]+),\n\s*(-?[\d\.eE\+\-]+),\n\s*"(.*?)"\n\s*\]"#).unwrap());
    static RE_2: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\n\s*(-?[\d\.eE\+\-]+),\n\s*(-?[\d\.eE\+\-]+)\n\s*\]"#).unwrap());

    for (i, spec) in data_list.iter().enumerate() {
        let mut map = serde_json::Map::new();

        for col in &columns {
            if col == "PEAKS_LIST" || col == "NUM PEAKS" { continue; }

            let mut val_str = "NaN".to_string();
            if let Some(val) = spec.metadata.get(col) {
                if !val.is_empty() && !val.eq_ignore_ascii_case("nan") { val_str = val.clone(); }
            }

            if col == "MSLEVEL" { if let Ok(num) = val_str.parse::<i64>() { map.insert(col.clone(), serde_json::json!(num)); continue; } }
            if ["PRECURSORMZ", "RT", "ENTROPY"].contains(&col.as_str()) {
                if let Ok(num) = val_str.parse::<f64>() { map.insert(col.clone(), serde_json::json!(num)); continue; }
            }
            map.insert(col.clone(), serde_json::Value::String(val_str));
        }

        let num_peaks_str = spec.metadata.get("NUM PEAKS").cloned().unwrap_or_else(|| "0".to_string());
        map.insert("NUM PEAKS".to_string(), serde_json::json!(num_peaks_str.parse::<i64>().unwrap_or(0)));

        let mut peaks_array = Vec::new();
        for &(mz, intensity) in &spec.peaks {
            peaks_array.push(serde_json::json!([mz, intensity]));
        }
        map.insert("PEAKS_LIST".to_string(), serde_json::Value::Array(peaks_array));

        let item_str_pretty = serde_json::to_string_pretty(&map).unwrap();
        let compacted_1 = RE_3.replace_all(&item_str_pretty, "[$1, $2, \"$3\"]").to_string();
        let compacted_2 = RE_2.replace_all(&compacted_1, "[$1, $2]").to_string();
        let indented_str = format!("  {}", compacted_2.replace('\n', "\n  "));

        file.write_all(indented_str.as_bytes())?;
        if i < len - 1 { file.write_all(b",\n")?; } else { file.write_all(b"\n")?; }

        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    file.write_all(b"]")?;
    file.flush()?;

    Ok(())
}

// ======================== ORCHESTRATEURS EXPOSÉS À PYTHON ========================

pub fn writting_msp_processing(
    py: Python, pos_lc: Vec<String>, pos_lc_insilico: Vec<String>, pos_gc: Vec<String>, pos_gc_insilico: Vec<String>, neg_lc: Vec<String>, neg_lc_insilico: Vec<String>, neg_gc: Vec<String>, neg_gc_insilico: Vec<String>, output_directory: &str, update: bool, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<()> {
    let sleep = || std::thread::sleep(std::time::Duration::from_millis(100));
    sleep(); write_msp(py, &pos_lc, "POS_LC.msp", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &pos_lc_insilico, "POS_LC_insilico.msp", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &pos_gc, "POS_GC.msp", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &pos_gc_insilico, "POS_GC_insilico.msp", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &neg_lc, "NEG_LC.msp", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &neg_lc_insilico, "NEG_LC_insilico.msp", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &neg_gc, "NEG_GC.msp", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_msp(py, &neg_gc_insilico, "NEG_GC_insilico.msp", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    Ok(())
}

pub fn writting_csv_processing(
    py: Python, pos_lc_df: Vec<Spectrum>, pos_gc_df: Vec<Spectrum>, neg_lc_df: Vec<Spectrum>, neg_gc_df: Vec<Spectrum>, pos_lc_df_insilico: Vec<Spectrum>, pos_gc_df_insilico: Vec<Spectrum>, neg_lc_df_insilico: Vec<Spectrum>, neg_gc_df_insilico: Vec<Spectrum>, ordered_columns: Vec<String>, output_directory: &str, update: bool, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<()> {
    let sleep = || std::thread::sleep(std::time::Duration::from_millis(100));
    sleep(); write_csv(py, &pos_lc_df, &ordered_columns, "POS_LC.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &pos_gc_df, &ordered_columns, "POS_GC.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_lc_df, &ordered_columns, "NEG_LC.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_gc_df, &ordered_columns, "NEG_GC.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &pos_lc_df_insilico, &ordered_columns, "POS_LC_In_Silico.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &pos_gc_df_insilico, &ordered_columns, "POS_GC_In_Silico.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_lc_df_insilico, &ordered_columns, "NEG_LC_In_Silico.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_gc_df_insilico, &ordered_columns, "NEG_GC_In_Silico.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    Ok(())
}

pub fn writting_json_processing(
    py: Python, update: bool, pos_lc_df: Vec<Spectrum>, pos_gc_df: Vec<Spectrum>, neg_lc_df: Vec<Spectrum>, neg_gc_df: Vec<Spectrum>, pos_lc_df_insilico: Vec<Spectrum>, pos_gc_df_insilico: Vec<Spectrum>, neg_lc_df_insilico: Vec<Spectrum>, neg_gc_df_insilico: Vec<Spectrum>, output_directory: &str, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<()> {
    let sleep = || std::thread::sleep(std::time::Duration::from_millis(100));
    sleep(); write_json(py, update, &pos_lc_df, "POS_LC.json", "POS", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &pos_gc_df, "POS_GC.json", "POS", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &neg_lc_df, "NEG_LC.json", "NEG", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &neg_gc_df, "NEG_GC.json", "NEG", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &pos_lc_df_insilico, "POS_LC_In_Silico.json", "POS", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &pos_gc_df_insilico, "POS_GC_In_Silico.json", "POS", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &neg_lc_df_insilico, "NEG_LC_In_Silico.json", "NEG", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_json(py, update, &neg_gc_df_insilico, "NEG_GC_In_Silico.json", "NEG", output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    Ok(())
}