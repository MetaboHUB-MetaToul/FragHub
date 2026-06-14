use std::collections::HashMap;

pub fn missing_precursormz_re_calculation(
    mut metadata_dict: HashMap<String, String>,
    context: &super::NormalizerContext
) -> HashMap<String, String> {

    // 1. Vérifier si on a besoin de recalculer
    let pmz_str = metadata_dict.get("PRECURSORMZ").cloned().unwrap_or_default();
    let needs_recalc = pmz_str.is_empty() || pmz_str.parse::<f64>().map_or(true, |v| v <= 0.0);

    if !needs_recalc {
        return metadata_dict;
    }

    // 2. Extraire les infos
    let adduct = metadata_dict.get("PRECURSORTYPE").cloned().unwrap_or_default();
    let inst_type = metadata_dict.get("INSTRUMENTTYPE").cloned().unwrap_or_default();

    if crate::globals_vars::GC_PATTERN.is_match(&inst_type) && adduct.is_empty() {
        return metadata_dict;
    }

    // 3. Trouver la différence de masse dans les dictionnaires après nettoyage de l'adduct
    let mass_diff = context.adduct_massdiff_pos.get(&adduct)
        .or_else(|| context.adduct_massdiff_neg.get(&adduct))
        .copied();

    if let Some(diff) = mass_diff {
        // 4. ON UTILISE UNIQUEMENT LA MASSE RDKIT GÉNÉRÉE PAR PYTHON
        if let Some(em) = metadata_dict.get("_RDKIT_EXACT_MASS").and_then(|v| v.parse::<f64>().ok()) {
            let new_pmz = em + diff;
            metadata_dict.insert("PRECURSORMZ".to_string(), new_pmz.to_string());
        }
        // 5. On supprime la clé temporaire pour ne pas polluer les données
        metadata_dict.remove("_RDKIT_EXACT_MASS");
    }

    metadata_dict
}