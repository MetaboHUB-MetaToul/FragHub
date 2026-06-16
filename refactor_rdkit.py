import re

with open('scripts/fraghub_rust/src/rdkit_bridge.rs', 'r') as f:
    content = f.read()

content = content.replace("use pyo3::prelude::*;\nuse pyo3::types::{PyDict, PyList, PyAny};", "use pyo3::prelude::*;\nuse pyo3::types::{PyList, PyAny};\nuse crate::spectrum::Spectrum;")

content = content.replace("#[pyfunction]\n#[pyo3(signature = (spectrum_list, output_directory, deletion_report, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]\n", "")

content = content.replace("pub fn process_mols<'py>(", "pub fn process_mols(")

content = content.replace("spectrum_list: &Bound<'py, PyList>,", "mut spectrum_list: Vec<Spectrum>,")
content = content.replace("-> PyResult<Bound<'py, PyList>> {", "-> PyResult<Vec<Spectrum>> {")

old_loop = """    let total = spectrum_list.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total, 0))?; }

    let valid_list = PyList::empty_bound(py);
    let mut deleted_count = 0;
    
    // Pour stocker les lignes supprimées
    let mut deleted_rows = Vec::new();
    let columns = vec!["FILENAME", "FILEHASH", "PREDICTED", "SPLASH", "SPECTRUMID", "RESOLUTION", "SYNON", "IONIZATION", "MSLEVEL", "FRAGMENTATIONMODE", "NAME", "PRECURSORMZ", "EXACTMASS", "AVERAGEMASS", "PRECURSORTYPE", "INSTRUMENTTYPE", "INSTRUMENT", "SMILES", "INCHI", "INCHIKEY", "COLLISIONENERGY", "FORMULA", "RT", "IONMODE", "COMMENT", "ENTROPY", "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS", "NPCLASS_PATHWAY", "NPCLASS_SUPERCLASS", "NPCLASS_CLASS", "NUM PEAKS", "PEAKS_LIST", "DELETION_REASON"];

    // Cache pour éviter de recalculer les mêmes molécules
    let mut cache: HashMap<String, HashMap<String, String>> = HashMap::new();

    for i in 0..total {
        let item = spectrum_list.get_item(i).unwrap();
        let dict = item.downcast::<PyDict>()?;
        
        let inchi = dict.get_item("INCHI").ok().flatten().and_then(|v| v.extract::<String>().ok()).unwrap_or_default();
        let smiles = dict.get_item("SMILES").ok().flatten().and_then(|v| v.extract::<String>().ok()).unwrap_or_default();
        
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
                dict.set_item(k, v)?;
            }
        }

        // Vérification finale
        let final_ik = dict.get_item("INCHIKEY").ok().flatten().and_then(|v| v.extract::<String>().ok()).unwrap_or_default();
        let final_em = dict.get_item("EXACTMASS").ok().flatten().and_then(|v| v.extract::<String>().ok()).unwrap_or_default();
        
        if INCHIKEY_PATTERN.is_match(&final_ik) && !final_em.is_empty() && final_em != "nan" {
            valid_list.append(&item)?;
        } else {
            deleted_count += 1;
            dict.set_item("DELETION_REASON", "spectrum deleted because it has neither inchi nor smiles nor inchikey, even after re calculation")?;
            
            let mut row_vals = Vec::new();
            for col in &columns {
                let val = dict.get_item(col).ok().flatten().and_then(|v| v.extract::<String>().ok()).unwrap_or_default();
                row_vals.push(val);
            }
            deleted_rows.push(row_vals);
        }

        if (i + 1) % 1000 == 0 {
            if let Some(cb) = &progress_callback { cb.call1(py, (i + 1,))?; }
        }
    }"""

new_loop = """    let total = spectrum_list.len();
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
    }"""

content = content.replace(old_loop, new_loop)

with open('scripts/fraghub_rust/src/rdkit_bridge.rs', 'w') as f:
    f.write(content)
