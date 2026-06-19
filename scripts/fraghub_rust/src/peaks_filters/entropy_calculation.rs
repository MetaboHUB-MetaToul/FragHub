// src/peaks_filters/entropy_calculation.rs

/// Calcule l'entropie de Shannon d'une liste de pics.
/// 
/// Pour un développeur Python : C'est l'équivalent exact de votre fonction optimisée avec `@jit(nopython=True)` via Numba.
/// En Rust, on passe un `&[f64]` (une *slice*, ou portion de tableau lue en lecture seule).
/// C'est plus léger que de passer un `Vec` car ça ne nécessite pas de posséder la mémoire.
///
/// # Arguments
/// * `peak_intensities` (&[f64]) : Tableau contenant uniquement les intensités des pics.
///
/// # Returns
/// * `f64` : Le score d'entropie calculé (float).
pub fn entropy_calculation(peak_intensities: &[f64]) -> f64 {
    // `.iter().sum()` additionne très efficacement toutes les valeurs.
    let total_intensity: f64 = peak_intensities.iter().sum();

    if total_intensity == 0.0 {
        return 0.0;
    }

    // En Rust, toute variable qui va être modifiée doit être explicitement déclarée `mut`.
    let mut entropy = 0.0;
    
    // Itération sur la slice. `&intensity` permet de récupérer la valeur f64 sans déréférencer manuellement.
    for &intensity in peak_intensities {
        let prob = intensity / total_intensity;
        if prob > 0.0 {
            // Equivalent strict de `-np.sum(probabilities * np.log2(probabilities))` en numpy.
            entropy -= prob * prob.log2();
        }
    }

    entropy // Retourne la valeur calculée sans mot clé `return`.
}