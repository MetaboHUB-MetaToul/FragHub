use pyo3::prelude::*;
use pyo3::types::{PyList, PyAny};
use crate::spectrum::Spectrum;
use std::collections::HashMap;
use crate::globals_vars::{INDIGO_SMILES_CORRECTION_PATTERN, INCHIKEY_PATTERN};
use std::fs;
use std::path::Path;

pub fn process_mols(
    py: Python,
    mut spectrum_list: Vec<Spectrum>,
    output_directory: &str,
    deletion_report: &pyo3::Bound<'_, pyo3::types::PyAny>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<Spectrum>> {

    if let Some(cb) = &prefix_callback { cb.call1(py, ("derivation and calculation (RDKit via Rust):",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }

    // 1. Importer RDKit via PyO3
    let chem = py.import_bound("rdkit.Chem")?;
    let exact_mol_wt = py.import_bound("rdkit.Chem.Descriptors")?.getattr("ExactMolWt")?;
    let mol_wt = py.import_bound("rdkit.Chem.Descriptors")?.getattr("MolWt")?;
    let calc_mol_formula = py.import_bound("rdkit.Chem.rdMolDescriptors")?.getattr("CalcMolFormula")?;

    let total = spectrum_list.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total, 0))?; }

    let mut valid_list = Vec::new();
    let mut deleted_count = 0;
    
    // Pour stocker les lignes supprimées
    let mut deleted_rows = Vec::new();
    let columns = vec!["FILENAME", "FILEHASH", "PREDICTED", "SPLASH", "SPECTRUMID", "RESOLUTION", "SYNON", "IONIZATION", "MSLEVEL", "FRAGMENTATIONMODE", "NAME", "PRECURSORMZ", "EXACTMASS", "AVERAGEMASS", "PRECURSORTYPE", "INSTRUMENTTYPE", "INSTRUMENT", "SMILES", "INCHI", "INCHIKEY", "COLLISIONENERGY", "FORMULA", "RT", "IONMODE", "COMMENT", "ENTROPY", "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS", "NPCLASS_PATHWAY", "NPCLASS_SUPERCLASS", "NPCLASS_CLASS", "NUM PEAKS", "PEAKS_LIST", "DELETION_REASON"];

    // Cache pour éviter de recalculer les mêmes molécules
    let mut cache: HashMap<String, HashMap<String, String>> = HashMap::new();

    for (i, mut spec) in spectrum_list.into_iter().enumerate() {
        let inchi = spec.metadata.get("INCHI").cloned().unwrap_or_default();
        let smiles = spec.metadata.get("SMILES").cloned().unwrap_or_default();
        
        let target_mol = if !inchi.is_empty() && inchi != "nan" { inchi.clone() } else { smiles.clone() };

        if !target_mol.is_empty() && target_mol != "nan" {
            let mut transforms = HashMap::new();

            if let Some(cached) = cache.get(&target_mol) {
                transforms = cached.clone();
            } else {
                let mut clean_mol = target_mol.clone();
                if !clean_mol.contains("InChI=") {
                    clean_mol = INDIGO_SMILES_CORRECTION_PATTERN.replace_all(&clean_mol, "").to_string();
                }

                // Essai de conversion RDKit
                let mol_obj = if clean_mol.contains("InChI=") {
                    chem.call_method1("MolFromInchi", (&clean_mol,))
                } else {
                    chem.call_method1("MolFromSmiles", (&clean_mol,))
                };

                if let Ok(mol) = mol_obj {
                    if !mol.is_none() {
                        if let Ok(i) = chem.call_method1("MolToInchi", (&mol,)) { transforms.insert("INCHI".to_string(), i.to_string()); }
                        if let Ok(ik) = chem.call_method1("MolToInchiKey", (&mol,)) { transforms.insert("INCHIKEY".to_string(), ik.to_string()); }
                        if let Ok(s) = chem.call_method1("MolToSmiles", (&mol,)) { transforms.insert("SMILES".to_string(), s.to_string()); }
                        if let Ok(f) = calc_mol_formula.call1((&mol,)) { transforms.insert("FORMULA".to_string(), f.to_string()); }
                        
                        // Recréation pour la masse (identique à Python)
                        let i_str = transforms.get("INCHI").unwrap_or(&"".to_string()).clone();
                        let s_str = transforms.get("SMILES").unwrap_or(&"".to_string()).clone();
                        let target_for_mass = if !i_str.is_empty() { i_str } else { s_str };
                        
                        let mol_mass_obj = if target_for_mass.contains("InChI=") {
                            chem.call_method1("MolFromInchi", (&target_for_mass,))
                        } else {
                            chem.call_method1("MolFromSmiles", (&target_for_mass,))
                        };

                        if let Ok(mol_mass) = mol_mass_obj {
                            if !mol_mass.is_none() {
                                if let Ok(em) = exact_mol_wt.call1((&mol_mass,)) { transforms.insert("EXACTMASS".to_string(), em.to_string()); }
                                if let Ok(am) = mol_wt.call1((&mol_mass,)) { transforms.insert("AVERAGEMASS".to_string(), am.to_string()); }
                            }
                        }
                    }
                }
                cache.insert(target_mol.clone(), transforms.clone());
            }

            // Appliquer les transformations
            for (k, v) in transforms {
                spec.metadata.insert(k, v);
            }
        }

        // Vérification finale
        let final_ik = spec.metadata.get("INCHIKEY").cloned().unwrap_or_default();
        let final_em = spec.metadata.get("EXACTMASS").cloned().unwrap_or_default();
        
        if INCHIKEY_PATTERN.is_match(&final_ik) && !final_em.is_empty() && final_em != "nan" {
            valid_list.push(spec);
        } else {
            deleted_count += 1;
            spec.metadata.insert("DELETION_REASON".to_string(), "spectrum deleted because it has neither inchi nor smiles nor inchikey, even after re calculation".to_string());
            
            let mut row_vals = Vec::new();
            for col in &columns {
                row_vals.push(spec.metadata.get(*col).cloned().unwrap_or_default());
            }
            deleted_rows.push(row_vals);
        }

        if (i + 1) % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (i + 1,))?; }
        }
    }

    if let Some(cb) = &progress_callback { cb.call1(py, (total,))?; }

    // Mise à jour du rapport de suppression
    if let Ok(current) = deletion_report.getattr("no_smiles_no_inchi_no_inchikey") {
        let current_val: i64 = current.extract().unwrap_or(0);
        deletion_report.setattr("no_smiles_no_inchi_no_inchikey", current_val + deleted_count)?;
    }

    // Écriture des suppressions si besoin
    if !deleted_rows.is_empty() {
        let del_dir = Path::new(output_directory).join("DELETED_SPECTRUMS");
        fs::create_dir_all(&del_dir).unwrap_or_default();
        let file_path = del_dir.join("deleted_no_inchi_smiles_inchikey_after_re_calculation.csv");
        
        let mut wtr = csv::WriterBuilder::new().delimiter(b'\t').from_path(file_path).unwrap();
        wtr.write_record(&columns).unwrap_or_default();
        for row in deleted_rows {
            wtr.write_record(&row).unwrap_or_default();
        }
        wtr.flush().unwrap_or_default();
    }

    Ok(valid_list)
}