// src/peaks_filters/check_minimum_peak_requiered.rs

/// Vérifie qu'un spectre contient un nombre minimum de pics.
/// 
/// Pour un développeur Python : Cette fonction filtre les spectres ayant trop peu d'informations.
/// Contrairement à Python où on lèverait une exception ou retournerait `None`, 
/// on retourne ici un vecteur vide `Vec::new()` pour indiquer que le spectre doit être ignoré,
/// et on met à jour la variable `deletion_reason`.
///
/// # Arguments
/// * `peaks` - Vecteur de tuples contenant `(m/z, intensité)`. Comparable à une `List[Tuple[float, float]]` en Python.
/// * `n_peaks` - Le nombre minimum de pics requis (type `usize` : entier positif utilisé pour les tailles/index en Rust).
/// * `deletion_reason` - Une référence mutable (`&mut`) vers un `Option<String>`. 
///   Équivalent Python : passer une liste ou un dict modifiable pour récupérer la raison de suppression.
///
/// # Returns
/// * `Vec<(f64, f64)>` : La liste des pics (vide si le minimum requis n'est pas atteint).
pub fn check_minimum_peak_requiered(
    peaks: Vec<(f64, f64)>,
    n_peaks: usize,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    if peaks.len() < n_peaks {
        // En Rust, l'étoile `*` permet de déréférencer le pointeur pour modifier la valeur pointée.
        // `Some(...)` est la manière Rust (sûre) de dire "il y a une valeur", contrairement à `None`.
        *deletion_reason = Some("spectrum deleted because its number of peaks is below the threshold chosen by the user".to_string());
        Vec::new() // Retourne un vecteur vide (sans utiliser le mot clé `return` à la fin d'un bloc).
    } else {
        peaks // Si tout va bien, on retourne la liste de pics intacte (ownership restitué).
    }
}