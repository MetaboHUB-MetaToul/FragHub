use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;
use csv::ReaderBuilder;
use std::path::Path;
use crate::global_state::STATE;

fn read_csv_to_dict_of_dicts(filepath: &str, sep: u8, key_col: &str) -> Result<HashMap<String, HashMap<String, String>>, Box<dyn std::error::Error + Send + Sync>> {
    let mut rdr = ReaderBuilder::new()
        .delimiter(sep)
        .quote(b'"')
        .from_path(filepath)?;

    let headers: Vec<String> = rdr.headers()?.iter().map(|s| s.to_string()).collect();
    let mut map = HashMap::new();

    let key_idx = headers.iter().position(|h| h == key_col);
    if key_idx.is_none() {
        return Ok(map);
    }
    let key_idx = key_idx.unwrap();

    for result in rdr.records() {
        if let Ok(record) = result {
            if let Some(key_val) = record.get(key_idx) {
                let mut row_dict = HashMap::new();
                for (i, val) in record.iter().enumerate() {
                    row_dict.insert(headers[i].clone(), val.to_string());
                }
                map.insert(key_val.to_string(), row_dict);
            }
        }
    }
    Ok(map)
}

/// Charge plusieurs fichiers CSV en parallèle.
///
/// Pour un développeur Python : C'est ici qu'on charge les bases de données (PubChem, Ontologies)
/// en RAM au démarrage de FragHub. Grâce à `par_iter()`, on lit tous les fichiers CSV
/// simultanément sur tous les cœurs du CPU.
fn read_multiple_csvs_to_dict(folder_path: &str, sep: u8, filter_str: &str, key_col: &str) -> HashMap<String, HashMap<String, String>> {
    let mut paths = Vec::new();
    if let Ok(entries) = fs::read_dir(folder_path) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_file() {
                if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                    if name.ends_with(".csv") && (filter_str.is_empty() || name.contains(filter_str)) {
                        paths.push(path.to_string_lossy().to_string());
                    }
                }
            }
        }
    }

    let results: Vec<_> = paths.par_iter().map(|p| {
        read_csv_to_dict_of_dicts(p, sep, key_col)
    }).collect();

    let mut merged: HashMap<String, HashMap<String, String>> = HashMap::new();
    for res in results {
        if let Ok(map) = res {
            for (k, v) in map {
                merged.insert(k, v);
            }
        }
    }
    merged
}

/// Point d'entrée pour le chargement des bases de données depuis Python.
///
/// Pour un développeur Python : Cette fonction est appelée au démarrage de l'app Electron/Python.
/// Elle peuple le dictionnaire `STATE` global (le cache RAM).
#[pyfunction]
pub fn load_internal_databases(_py: Python, base_dir: &str) -> PyResult<()> {
    let base_path = Path::new(base_dir);

    // 1. Pubchem
    let pubchem_path = base_path.join("datas").join("pubchem_datas");
    let pubchem_datas = read_multiple_csvs_to_dict(&pubchem_path.to_string_lossy(), b';', "pubchem_rdkit_clean_part", "INCHIKEY");

    // 2. Ontologies
    let ontologies_path = base_path.join("datas").join("ontologies_datas");
    let ontologies_datas = read_multiple_csvs_to_dict(&ontologies_path.to_string_lossy(), b';', "ontologies_dict", "INCHIKEY");

    // 3. Adducts
    let adduct_file_path = base_path.join("datas").join("adduct_to_convert.csv");
    let mut adduct_dict_pos = HashMap::new();
    let mut adduct_massdiff_dict_pos = HashMap::new();
    let mut adduct_dict_neg = HashMap::new();
    let mut adduct_massdiff_dict_neg = HashMap::new();

    if let Ok(mut rdr) = ReaderBuilder::new().delimiter(b';').from_path(&adduct_file_path) {
        if let Ok(headers) = rdr.headers() {
            let headers = headers.clone();
            let mut idx_known = 0; let mut idx_default = 1; let mut idx_massdiff = 2; let mut idx_ionmode = 3;
            for (i, h) in headers.iter().enumerate() {
                match h {
                    "known_adduct" => idx_known = i,
                    "fraghub_default" => idx_default = i,
                    "massdiff" => idx_massdiff = i,
                    "ionmode" => idx_ionmode = i,
                    _ => {}
                }
            }
            for result in rdr.records() {
                if let Ok(record) = result {
                    let known = record.get(idx_known).unwrap_or("").to_string();
                    let default = record.get(idx_default).unwrap_or("").to_string();
                    let massdiff_str = record.get(idx_massdiff).unwrap_or("0.0");
                    let massdiff: f64 = massdiff_str.parse().unwrap_or(0.0);
                    let ionmode = record.get(idx_ionmode).unwrap_or("");
                    if ionmode == "positive" {
                        adduct_dict_pos.insert(known.clone(), default.clone());
                        adduct_massdiff_dict_pos.insert(default.clone(), massdiff);
                    } else if ionmode == "negative" {
                        adduct_dict_neg.insert(known.clone(), default.clone());
                        adduct_massdiff_dict_neg.insert(default.clone(), massdiff);
                    }
                }
            }
        }
    }

    // 4. Keys
    let keys_file_path = base_path.join("datas").join("key_to_convert.csv");
    let mut keys_dict = HashMap::new();
    if let Ok(mut rdr) = ReaderBuilder::new().delimiter(b';').from_path(&keys_file_path) {
        if let Ok(headers) = rdr.headers() {
            let headers = headers.clone();
            let mut idx_known = 0; let mut idx_default = 1;
            for (i, h) in headers.iter().enumerate() {
                match h {
                    "known_synonym" => idx_known = i,
                    "fraghub_default" => idx_default = i,
                    _ => {}
                }
            }
            for result in rdr.records() {
                if let Ok(record) = result {
                    let known = record.get(idx_known).unwrap_or("").to_string();
                    let default = record.get(idx_default).unwrap_or("").to_uppercase();
                    keys_dict.insert(known, default);
                }
            }
        }
    }

    // 5. Instrument tree
    let instrument_tree_path = base_path.join("datas").join("instruments_tree.json");
    let instrument_tree: serde_json::Value = if let Ok(content) = fs::read_to_string(&instrument_tree_path) {
        serde_json::from_str(&content).unwrap_or(serde_json::Value::Null)
    } else {
        serde_json::Value::Null
    };

    // Update global state
    if let Ok(mut state) = STATE.write() {
        state.pubchem_datas = pubchem_datas;
        state.ontologies_datas = ontologies_datas;
        state.adduct_dict_pos = adduct_dict_pos;
        state.adduct_massdiff_dict_pos = adduct_massdiff_dict_pos;
        state.adduct_dict_neg = adduct_dict_neg;
        state.adduct_massdiff_dict_neg = adduct_massdiff_dict_neg;
        state.keys_dict = keys_dict;
        state.instrument_tree = instrument_tree;
    }

    Ok(())
}
