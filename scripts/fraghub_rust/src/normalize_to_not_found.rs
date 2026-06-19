use pyo3::prelude::*;
use crate::spectrum::Spectrum;

/// Remplace toutes les valeurs vides des métadonnées par "NOT FOUND".
///
/// Pour un développeur Python : Observez `iter_mut()` et `values_mut()`.
/// En Rust, on doit demander explicitement la permission de modifier (mut) des valeurs.
/// Le `*val = ...` déréférence le pointeur vers la valeur pour y écrire "NOT FOUND"
/// directement dans la mémoire, sans avoir à créer un nouveau dictionnaire ni perdre de temps.
pub fn normalize_to_not_found_processing(
    _py: Python,
    mut spectrum_list: Vec<Spectrum>,
) -> PyResult<Vec<Spectrum>> {
    for spec in spectrum_list.iter_mut() {
        for val in spec.metadata.values_mut() {
            if val.is_empty() {
                *val = "NOT FOUND".to_string();
            }
        }
    }
    Ok(spectrum_list)
}