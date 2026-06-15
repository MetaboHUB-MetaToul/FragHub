// src/writers.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyAny};
use std::fs::{self, OpenOptions};
use std::io::{Write, Seek, SeekFrom, Read};
use std::path::Path;
use csv::WriterBuilder;
use once_cell::sync::Lazy;
use regex::Regex;

// Fonction utilitaire pour extraire "NOT FOUND" si vide
fn get_str<'py>(dict: &Bound<'py, PyDict>, key: &str) -> String {
    if let Ok(Some(val)) = dict.get_item(key) {
        let s = val.extract::<String>().unwrap_or_else(|_| val.to_string());
        if !s.trim().is_empty() && s.to_lowercase() != "nan" {
            return s;
        }
    }
    "NOT FOUND".to_string()
}

fn write_msp<'py>(
    py: Python<'py>,
    spectrum_list: &Bound<'py, PyList>,
    filename: &str,
    mode: &str,
    update: bool,
    output_directory: &str,
    progress_callback: &Option<PyObject>,
    total_items_callback: &Option<PyObject>,
    prefix_callback: &Option<PyObject>,
    item_type_callback: &Option<PyObject>,
) -> PyResult<()> {

    let len = spectrum_list.len();
    if len == 0 { return Ok(()); }

    let path_dir = Path::new(output_directory).join("MSP").join(mode);
    fs::create_dir_all(&path_dir)?;
    let file_path = path_dir.join(filename);

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Writing {} to MSP:", filename),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("spectra",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .append(update)
        .truncate(!update)
        .open(&file_path)?;

    for i in 0..len {
        if let Ok(item) = spectrum_list.get_item(i) {
            if let Ok(spec_str) = item.extract::<String>() {
                file.write_all(spec_str.as_bytes())?;
                file.write_all(b"\n\n")?;
            }
        }
        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    file.flush()?;
    Ok(())
}

fn write_csv<'py>(
    py: Python<'py>,
    df: &Bound<'py, PyAny>,
    filename: &str,
    mode: &str,
    update: bool,
    output_directory: &str,
    progress_callback: &Option<PyObject>,
    total_items_callback: &Option<PyObject>,
    prefix_callback: &Option<PyObject>,
    item_type_callback: &Option<PyObject>,
) -> PyResult<()> {

    let len: usize = df.call_method0("__len__")?.extract()?;
    if len == 0 { return Ok(()); }

    let path_dir = Path::new(output_directory).join("CSV").join(mode);
    fs::create_dir_all(&path_dir)?;
    let file_path = path_dir.join(filename);

    if let Some(cb) = prefix_callback { cb.call1(py, (format!("Writing {} to CSV:", filename),))?; }
    if let Some(cb) = item_type_callback { cb.call1(py, ("rows",))?; }
    if let Some(cb) = total_items_callback { cb.call1(py, (len, 0))?; }

    let columns_py = df.getattr("columns")?;
    let columns: Vec<String> = columns_py.extract()?;

    let is_append = update && file_path.exists();
    let file = OpenOptions::new().write(true).create(true).append(is_append).truncate(!is_append).open(&file_path)?;
    let mut wtr = WriterBuilder::new().delimiter(b'\t').quote(b'"').has_headers(!is_append).from_writer(file);

    // CORRECTION : On convertit explicitement l'erreur CSV en erreur d'entrée/sortie Python
    if !is_append {
        wtr.write_record(&columns).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
    }

    let dict_list_py = df.call_method1("to_dict", ("records",))?;
    let records = dict_list_py.downcast::<PyList>()?;

    for i in 0..len {
        if let Ok(item) = records.get_item(i) {
            if let Ok(dict) = item.downcast::<PyDict>() {
                let mut record_row = Vec::with_capacity(columns.len());
                for col in &columns {
                    let mut val_str = String::new();
                    if let Ok(Some(val)) = dict.get_item(col) {
                        val_str = val.extract::<String>().unwrap_or_else(|_| val.to_string());
                        if val_str.to_lowercase() == "nan" { val_str = String::new(); }
                        if col == "PEAKS_LIST" { val_str = val_str.replace('\n', ";"); }
                    }
                    record_row.push(val_str);
                }
                // CORRECTION : Même chose ici pour l'écriture de la ligne
                wtr.write_record(&record_row).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;
            }
        }
        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }
    wtr.flush()?;
    Ok(())
}

fn write_json<'py>(
    py: Python<'py>,
    update: bool,
    df: &Bound<'py, PyAny>,
    filename: &str,
    mode: &str,
    output_directory: &str,
    progress_callback: &Option<PyObject>,
    total_items_callback: &Option<PyObject>,
    prefix_callback: &Option<PyObject>,
    item_type_callback: &Option<PyObject>,
) -> PyResult<()> {

    let len: usize = df.call_method0("__len__")?.extract()?;
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

    let dict_list_py = df.call_method1("to_dict", ("records",))?;
    let records = dict_list_py.downcast::<PyList>()?;

    static RE_3: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\n\s*(-?[\d\.eE\+\-]+),\n\s*(-?[\d\.eE\+\-]+),\n\s*"(.*?)"\n\s*\]"#).unwrap());
    static RE_2: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\n\s*(-?[\d\.eE\+\-]+),\n\s*(-?[\d\.eE\+\-]+)\n\s*\]"#).unwrap());

    for i in 0..len {
        let item = records.get_item(i).unwrap();
        let dict = item.downcast::<PyDict>()?;
        let mut map = serde_json::Map::new();

        for (k, v) in dict.iter() {
            let key = k.extract::<String>()?;
            if key == "PEAKS_LIST" || key == "NUM PEAKS" { continue; }

            let val_str = v.extract::<String>().unwrap_or_else(|_| v.to_string());
            if val_str.to_lowercase() == "nan" || val_str.is_empty() {
                map.insert(key, serde_json::Value::String("NaN".to_string()));
                continue;
            }

            if key == "MSLEVEL" { if let Ok(num) = val_str.parse::<i64>() { map.insert(key, serde_json::json!(num)); continue; } }
            if ["PRECURSORMZ", "RT", "ENTROPY"].contains(&key.as_str()) {
                if let Ok(num) = val_str.parse::<f64>() {
                    if num.is_nan() || num.is_infinite() {
                        map.insert(key, serde_json::Value::String("NaN".to_string()));
                    } else {
                        map.insert(key, serde_json::json!(num));
                    }
                    continue;
                }
            }
            map.insert(key, serde_json::Value::String(val_str));
        }

        let num_peaks_str = get_str(dict, "NUM PEAKS");
        map.insert("NUM PEAKS".to_string(), serde_json::json!(num_peaks_str.parse::<i64>().unwrap_or(0)));

        let peaks_str = get_str(dict, "PEAKS_LIST");
        let mut peaks_array = Vec::new();

        if peaks_str != "NOT FOUND" && !peaks_str.is_empty() {
            let pairs: Vec<&str> = if peaks_str.contains(';') {
                peaks_str.trim().split(';').collect()
            } else {
                peaks_str.trim().split('\n').collect()
            };

            for pair in pairs {
                let parts: Vec<&str> = pair.split_whitespace().collect();
                if parts.len() >= 2 {
                    if let (Ok(mz), Ok(intensity)) = (parts[0].parse::<f64>(), parts[1].parse::<f64>()) {
                        if parts.len() == 3 { peaks_array.push(serde_json::json!([mz, intensity, parts[2]])); }
                        else { peaks_array.push(serde_json::json!([mz, intensity])); }
                    }
                }
            }
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

#[pyfunction]
#[pyo3(signature = (pos_lc, pos_lc_insilico, pos_gc, pos_gc_insilico, neg_lc, neg_lc_insilico, neg_gc, neg_gc_insilico, output_directory, update=false, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
#[allow(clippy::too_many_arguments)]
pub fn writting_msp_processing<'py>(
    py: Python<'py>, pos_lc: Bound<'py, PyList>, pos_lc_insilico: Bound<'py, PyList>, pos_gc: Bound<'py, PyList>, pos_gc_insilico: Bound<'py, PyList>, neg_lc: Bound<'py, PyList>, neg_lc_insilico: Bound<'py, PyList>, neg_gc: Bound<'py, PyList>, neg_gc_insilico: Bound<'py, PyList>, output_directory: &str, update: bool, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<()> {
    // CORRECTION : on supprime 'mut'
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

#[pyfunction]
#[pyo3(signature = (pos_lc_df, pos_gc_df, neg_lc_df, neg_gc_df, pos_lc_df_insilico, pos_gc_df_insilico, neg_lc_df_insilico, neg_gc_df_insilico, output_directory, update=false, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
#[allow(clippy::too_many_arguments)]
pub fn writting_csv_processing<'py>(
    py: Python<'py>, pos_lc_df: Bound<'py, PyAny>, pos_gc_df: Bound<'py, PyAny>, neg_lc_df: Bound<'py, PyAny>, neg_gc_df: Bound<'py, PyAny>, pos_lc_df_insilico: Bound<'py, PyAny>, pos_gc_df_insilico: Bound<'py, PyAny>, neg_lc_df_insilico: Bound<'py, PyAny>, neg_gc_df_insilico: Bound<'py, PyAny>, output_directory: &str, update: bool, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<()> {
    // CORRECTION : on supprime 'mut'
    let sleep = || std::thread::sleep(std::time::Duration::from_millis(100));
    sleep(); write_csv(py, &pos_lc_df, "POS_LC.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &pos_gc_df, "POS_GC.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_lc_df, "NEG_LC.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_gc_df, "NEG_GC.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &pos_lc_df_insilico, "POS_LC_In_Silico.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &pos_gc_df_insilico, "POS_GC_In_Silico.csv", "POS", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_lc_df_insilico, "NEG_LC_In_Silico.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    sleep(); write_csv(py, &neg_gc_df_insilico, "NEG_GC_In_Silico.csv", "NEG", update, output_directory, &progress_callback, &total_items_callback, &prefix_callback, &item_type_callback)?;
    Ok(())
}

#[pyfunction]
#[pyo3(signature = (update, pos_lc_df, pos_gc_df, neg_lc_df, neg_gc_df, pos_lc_df_insilico, pos_gc_df_insilico, neg_lc_df_insilico, neg_gc_df_insilico, output_directory, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
#[allow(clippy::too_many_arguments)]
pub fn writting_json_processing<'py>(
    py: Python<'py>, update: bool, pos_lc_df: Bound<'py, PyAny>, pos_gc_df: Bound<'py, PyAny>, neg_lc_df: Bound<'py, PyAny>, neg_gc_df: Bound<'py, PyAny>, pos_lc_df_insilico: Bound<'py, PyAny>, pos_gc_df_insilico: Bound<'py, PyAny>, neg_lc_df_insilico: Bound<'py, PyAny>, neg_gc_df_insilico: Bound<'py, PyAny>, output_directory: &str, progress_callback: Option<PyObject>, total_items_callback: Option<PyObject>, prefix_callback: Option<PyObject>, item_type_callback: Option<PyObject>,
) -> PyResult<()> {
    // CORRECTION : on supprime 'mut'
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