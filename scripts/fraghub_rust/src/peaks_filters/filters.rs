// src/peaks_filters/filters.rs
use std::collections::HashMap;

/// Filtre optimisé pour supprimer les pics <= 0.0
pub fn remove_non_positive_peaks(mut peak_array: Vec<(f64, f64)>) -> Vec<(f64, f64)> {
    peak_array.retain(|&(_mz, intensity)| intensity > 0.0);
    peak_array
}

pub fn apply_filters(
    mut peak_array: Vec<(f64, f64)>,
    _precursormz: Option<f64>,
    _parameters_dict: &HashMap<String, f64>,
    _deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {

    // --- Step 1: Mandatory filter ---
    peak_array = remove_non_positive_peaks(peak_array);

    // --- Step 2: Apply conditional filters ---
    // (Nous ajouterons les appels aux autres filtres mathématiques ici lors des prochaines étapes)

    peak_array
}