import re

with open('scripts/fraghub_rust/src/writers.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyList, PyDict, PyAny};", "use pyo3::prelude::*;\nuse crate::spectrum::Spectrum;")

# For write_msp, spectrum_list is a Bound<'py, PyList> containing String items. Wait, the `csv_to_msp_processing` returned `Vec<String>`.
# So `write_msp` should take `&Vec<String>`.
content = content.replace("fn write_msp<'py>(", "fn write_msp(")
content = content.replace("py: Python<'py>, spectrum_list: &Bound<'py, PyList>,", "py: Python, spectrum_list: &Vec<String>,")
old_write_msp_loop = """    for i in 0..len {
        if let Ok(item) = spectrum_list.get_item(i) {
            if let Ok(spec_str) = item.extract::<String>() {
                file.write_all(spec_str.as_bytes())?;
                file.write_all(b"\\n\\n")?;
            }
        }
        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }"""
new_write_msp_loop = """    for (i, spec_str) in spectrum_list.iter().enumerate() {
        file.write_all(spec_str.as_bytes())?;
        file.write_all(b"\\n\\n")?;
        
        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }"""
content = content.replace(old_write_msp_loop, new_write_msp_loop)

# For write_csv, data_list is &Bound<'py, PyList>. Should be &Vec<Spectrum>.
content = content.replace("fn write_csv<'py>(", "fn write_csv(")
content = content.replace("py: Python<'py>, data_list: &Bound<'py, PyList>,", "py: Python, data_list: &Vec<Spectrum>,")
old_write_csv_loop = """    for i in 0..len {
        let item = data_list.get_item(i)?;
        let dict = item.downcast::<PyDict>()?;
        let mut row = Vec::with_capacity(ordered_columns.len());

        for col in ordered_columns {
            let mut cell_val = String::new();
            if let Ok(Some(val)) = dict.get_item(col.as_str()) {
                if let Ok(s) = val.extract::<String>() {
                    if !s.eq_ignore_ascii_case("nan") {
                        cell_val = s;
                        if col == "PEAKS_LIST" { cell_val = cell_val.replace('\\n', ";"); }
                    }
                } else if let Ok(num) = val.extract::<f64>() {
                    if !num.is_nan() { cell_val = num.to_string(); }
                } else if let Ok(num) = val.extract::<i64>() {
                    cell_val = num.to_string();
                }
            }
            row.push(cell_val);
        }
        wtr.write_record(&row).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))?;

        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }"""
new_write_csv_loop = """    for (i, spec) in data_list.iter().enumerate() {
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
    }"""
content = content.replace(old_write_csv_loop, new_write_csv_loop)


# For write_json, data_list is &Bound<'py, PyList>. Should be &Vec<Spectrum>.
content = content.replace("fn write_json<'py>(", "fn write_json(")
content = content.replace("py: Python<'py>, update: bool, data_list: &Bound<'py, PyList>,", "py: Python, update: bool, data_list: &Vec<Spectrum>,")

old_write_json_loop = """    // Récupération dynamique des clés du premier dictionnaire pour le JSON
    let first_item = data_list.get_item(0)?;
    let first_dict = first_item.downcast::<PyDict>()?;
    let columns: Vec<String> = first_dict.keys().extract()?;

    static RE_3: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\\n\\s*(-?[\\d\\.eE\\+\\-]+),\\n\\s*(-?[\\d\\.eE\\+\\-]+),\\n\\s*"(.*?)"\\n\\s*\\]"#).unwrap());
    static RE_2: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\\n\\s*(-?[\\d\\.eE\\+\\-]+),\\n\\s*(-?[\\d\\.eE\\+\\-]+)\\n\\s*\\]"#).unwrap());

    for i in 0..len {
        let item = data_list.get_item(i)?;
        let dict = item.downcast::<PyDict>()?;
        let mut map = serde_json::Map::new();

        for col in &columns {
            if col == "PEAKS_LIST" || col == "NUM PEAKS" { continue; }

            let mut val_str = "NaN".to_string();
            if let Ok(Some(val)) = dict.get_item(col.as_str()) {
                if let Ok(s) = val.extract::<String>() {
                    if !s.is_empty() && !s.eq_ignore_ascii_case("nan") { val_str = s; }
                } else if let Ok(num) = val.extract::<f64>() {
                    if !num.is_nan() { val_str = num.to_string(); }
                } else if let Ok(num) = val.extract::<i64>() {
                    val_str = num.to_string();
                }
            }

            if col == "MSLEVEL" { if let Ok(num) = val_str.parse::<i64>() { map.insert(col.clone(), serde_json::json!(num)); continue; } }
            if ["PRECURSORMZ", "RT", "ENTROPY"].contains(&col.as_str()) {
                if let Ok(num) = val_str.parse::<f64>() { map.insert(col.clone(), serde_json::json!(num)); continue; }
            }
            map.insert(col.clone(), serde_json::Value::String(val_str));
        }

        let num_peaks_str = if let Ok(Some(val)) = dict.get_item("NUM PEAKS") { val.extract::<String>().unwrap_or_else(|_| "0".to_string()) } else { "0".to_string() };
        map.insert("NUM PEAKS".to_string(), serde_json::json!(num_peaks_str.parse::<i64>().unwrap_or(0)));

        let mut peaks_array = Vec::new();
        if let Ok(Some(val)) = dict.get_item("PEAKS_LIST") {
            if let Ok(peaks_str) = val.extract::<String>() {
                if !peaks_str.is_empty() && !peaks_str.eq_ignore_ascii_case("nan") && peaks_str != "NOT FOUND" {
                    let pairs: Vec<&str> = if peaks_str.contains(';') { peaks_str.trim().split(';').collect() } else { peaks_str.trim().split('\\n').collect() };
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
            }
        }
        map.insert("PEAKS_LIST".to_string(), serde_json::Value::Array(peaks_array));

        let item_str_pretty = serde_json::to_string_pretty(&map).unwrap();
        let compacted_1 = RE_3.replace_all(&item_str_pretty, "[$1, $2, \\"$3\\"]").to_string();
        let compacted_2 = RE_2.replace_all(&compacted_1, "[$1, $2]").to_string();
        let indented_str = format!("  {}", compacted_2.replace('\\n', "\\n  "));

        file.write_all(indented_str.as_bytes())?;
        if i < len - 1 { file.write_all(b",\\n")?; } else { file.write_all(b"\\n")?; }

        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }"""

new_write_json_loop = """    // Récupération dynamique des clés du premier dictionnaire pour le JSON
    let first_spec = &data_list[0];
    let columns: Vec<String> = first_spec.metadata.keys().cloned().collect();

    static RE_3: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\\n\\s*(-?[\\d\\.eE\\+\\-]+),\\n\\s*(-?[\\d\\.eE\\+\\-]+),\\n\\s*"(.*?)"\\n\\s*\\]"#).unwrap());
    static RE_2: Lazy<Regex> = Lazy::new(|| Regex::new(r#"\[\\n\\s*(-?[\\d\\.eE\\+\\-]+),\\n\\s*(-?[\\d\\.eE\\+\\-]+)\\n\\s*\\]"#).unwrap());

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
        let compacted_1 = RE_3.replace_all(&item_str_pretty, "[$1, $2, \\"$3\\"]").to_string();
        let compacted_2 = RE_2.replace_all(&compacted_1, "[$1, $2]").to_string();
        let indented_str = format!("  {}", compacted_2.replace('\\n', "\\n  "));

        file.write_all(indented_str.as_bytes())?;
        if i < len - 1 { file.write_all(b",\\n")?; } else { file.write_all(b"\\n")?; }

        if let Some(cb) = progress_callback {
            if (i + 1) % 500 == 0 || i == len - 1 { cb.call1(py, (i + 1,))?; }
        }
    }"""
content = content.replace(old_write_json_loop, new_write_json_loop)


content = content.replace("#[pyfunction]\n#[pyo3(signature = (pos_lc, pos_lc_insilico, pos_gc, pos_gc_insilico, neg_lc, neg_lc_insilico, neg_gc, neg_gc_insilico, output_directory, update=false, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n#[allow(clippy::too_many_arguments)]\n", "")
content = content.replace("pub fn writting_msp_processing<'py>(", "pub fn writting_msp_processing(")
content = content.replace("py: Python<'py>, pos_lc: Bound<'py, PyList>, pos_lc_insilico: Bound<'py, PyList>, pos_gc: Bound<'py, PyList>, pos_gc_insilico: Bound<'py, PyList>, neg_lc: Bound<'py, PyList>, neg_lc_insilico: Bound<'py, PyList>, neg_gc: Bound<'py, PyList>, neg_gc_insilico: Bound<'py, PyList>,",
                          "py: Python, pos_lc: Vec<String>, pos_lc_insilico: Vec<String>, pos_gc: Vec<String>, pos_gc_insilico: Vec<String>, neg_lc: Vec<String>, neg_lc_insilico: Vec<String>, neg_gc: Vec<String>, neg_gc_insilico: Vec<String>,")

content = content.replace("#[pyfunction]\n#[pyo3(signature = (pos_lc_df, pos_gc_df, neg_lc_df, neg_gc_df, pos_lc_df_insilico, pos_gc_df_insilico, neg_lc_df_insilico, neg_gc_df_insilico, ordered_columns, output_directory, update=false, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n#[allow(clippy::too_many_arguments)]\n", "")
content = content.replace("pub fn writting_csv_processing<'py>(", "pub fn writting_csv_processing(")
content = content.replace("py: Python<'py>, pos_lc_df: Bound<'py, PyList>, pos_gc_df: Bound<'py, PyList>, neg_lc_df: Bound<'py, PyList>, neg_gc_df: Bound<'py, PyList>, pos_lc_df_insilico: Bound<'py, PyList>, pos_gc_df_insilico: Bound<'py, PyList>, neg_lc_df_insilico: Bound<'py, PyList>, neg_gc_df_insilico: Bound<'py, PyList>,",
                          "py: Python, pos_lc_df: Vec<Spectrum>, pos_gc_df: Vec<Spectrum>, neg_lc_df: Vec<Spectrum>, neg_gc_df: Vec<Spectrum>, pos_lc_df_insilico: Vec<Spectrum>, pos_gc_df_insilico: Vec<Spectrum>, neg_lc_df_insilico: Vec<Spectrum>, neg_gc_df_insilico: Vec<Spectrum>,")


content = content.replace("#[pyfunction]\n#[pyo3(signature = (update, pos_lc_df, pos_gc_df, neg_lc_df, neg_gc_df, pos_lc_df_insilico, pos_gc_df_insilico, neg_lc_df_insilico, neg_gc_df_insilico, output_directory, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n#[allow(clippy::too_many_arguments)]\n", "")
content = content.replace("pub fn writting_json_processing<'py>(", "pub fn writting_json_processing(")
content = content.replace("py: Python<'py>, update: bool, pos_lc_df: Bound<'py, PyList>, pos_gc_df: Bound<'py, PyList>, neg_lc_df: Bound<'py, PyList>, neg_gc_df: Bound<'py, PyList>, pos_lc_df_insilico: Bound<'py, PyList>, pos_gc_df_insilico: Bound<'py, PyList>, neg_lc_df_insilico: Bound<'py, PyList>, neg_gc_df_insilico: Bound<'py, PyList>,",
                          "py: Python, update: bool, pos_lc_df: Vec<Spectrum>, pos_gc_df: Vec<Spectrum>, neg_lc_df: Vec<Spectrum>, neg_gc_df: Vec<Spectrum>, pos_lc_df_insilico: Vec<Spectrum>, pos_gc_df_insilico: Vec<Spectrum>, neg_lc_df_insilico: Vec<Spectrum>, neg_gc_df_insilico: Vec<Spectrum>,")

with open('scripts/fraghub_rust/src/writers.rs', 'w') as f:
    f.write(content)
