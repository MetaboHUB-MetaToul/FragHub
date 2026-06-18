use std::collections::HashMap;
use pyo3::prelude::*;
use regex::Regex;
use once_cell::sync::Lazy;

static IE_EI_PATTERN: Lazy<Regex> = Lazy::new(|| Regex::new(r"(?i)\b(IE|EI)\b").unwrap());

fn get_exact_mass_from_rdkit(inchi: &str, smiles: &str) -> Option<f64> {
    Python::with_gil(|py| {
        // Désactiver les logs rdkit comme en Python
        if let Ok(rdlogger) = py.import_bound("rdkit.RDLogger") {
            let _ = rdlogger.call_method1("DisableLog", ("rdApp.*",));
        }

        let chem = py.import_bound("rdkit.Chem").ok()?;
        let descriptors = py.import_bound("rdkit.Chem.Descriptors").ok()?;

        let mol = if !inchi.is_empty() && inchi.contains("InChI=") {
            chem.call_method1("MolFromInchi", (inchi,)).ok()
        } else if !smiles.is_empty() {
            chem.call_method1("MolFromSmiles", (smiles,)).ok()
        } else {
            None
        };

        if let Some(mol) = mol {
            if !mol.is_none() {
                if let Ok(mass_obj) = descriptors.call_method1("ExactMolWt", (&mol,)) {
                    return mass_obj.extract::<f64>().ok();
                }
            }
        }
        None
    })
}

pub fn missing_precursormz_re_calculation(
    mut metadata_dict: HashMap<String, String>,
    context: &super::NormalizerContext
) -> HashMap<String, String> {

    // 1. Vérifier si on a besoin de recalculer
    let pmz_str = metadata_dict.get("PRECURSORMZ").cloned().unwrap_or_default();
    let mut needs_recalc = false;

    if pmz_str.is_empty() {
        needs_recalc = true;
    } else if let Some(caps) = crate::globals_vars::FLOAT_CHECK_PATTERN.captures(&pmz_str) {
        let matched_str = caps.get(1).unwrap().as_str().replace(',', ".");
        if let Ok(val) = matched_str.parse::<f64>() {
            if val <= 0.0 { needs_recalc = true; }
        } else { needs_recalc = true; }
    } else {
        needs_recalc = true;
    }

    if !needs_recalc {
        return metadata_dict;
    }

    // 2. Extraire les infos pour la différence de masse
    let adduct = metadata_dict.get("PRECURSORTYPE").cloned().unwrap_or_default();
    let inst_type = metadata_dict.get("INSTRUMENTTYPE").cloned().unwrap_or_default();

    if IE_EI_PATTERN.is_match(&inst_type) && adduct.is_empty() {
        return metadata_dict;
    }

    let mass_diff = context.adduct_massdiff_pos.get(&adduct)
        .or_else(|| context.adduct_massdiff_neg.get(&adduct))
        .copied();

    // 3. Calculer avec RDKit (via PyO3) si une différence de masse est trouvée
    if let Some(diff) = mass_diff {
        let inchi = metadata_dict.get("INCHI").cloned().unwrap_or_default();
        let smiles = metadata_dict.get("SMILES").cloned().unwrap_or_default();

        if let Some(em) = get_exact_mass_from_rdkit(&inchi, &smiles) {
            let new_pmz = em + diff;
            metadata_dict.insert("PRECURSORMZ".to_string(), new_pmz.to_string());
        }
    }

    metadata_dict
}