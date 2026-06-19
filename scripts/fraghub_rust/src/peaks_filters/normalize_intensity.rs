// src/peaks_filters/normalize_intensity.rs

/// Normalise l'intensité des pics de sorte que le pic le plus intense ait une valeur de 1.0.
/// 
/// Pour un développeur Python : En Python on ferait `max_int = max([p[1] for p in peaks])`.
/// En Rust, on utilise un concept fonctionnel puissant : les Itérateurs.
///
/// # Arguments
/// * `peaks` (Vec<(f64, f64)>) : Le vecteur `mut`able de pics.
///
/// # Returns
/// * `Vec<(f64, f64)>` : La liste des pics normalisés.
pub fn normalize_intensity(mut peaks: Vec<(f64, f64)>) -> Vec<(f64, f64)> {
    if peaks.is_empty() {
        return peaks; // Sortie prématurée avec `return`.
    }

    // 1. `.iter()` : Crée un itérateur sur les éléments (sans les consommer).
    // 2. `.map(|p| p.1)` : Extrait seulement la deuxième valeur (l'intensité).
    // 3. `.fold(0.0_f64, f64::max)` : Équivalent de `reduce` en Python. 
    //    Part de 0.0 et garde à chaque étape le maximum entre l'accumulateur et la valeur courante.
    let max_int = peaks.iter().map(|p| p.1).fold(0.0_f64, f64::max);

    if max_int != 0.0 {
        // On itère avec `&mut` (référence mutable) pour modifier chaque pic in-place.
        for p in &mut peaks {
            p.1 /= max_int; // p.1 représente la deuxième valeur du tuple (intensité).
        }
        peaks
    } else {
        Vec::new()
    }
}