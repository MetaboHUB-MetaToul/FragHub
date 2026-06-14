// src/peaks_filters/entropy_calculation.rs

/// Calcule l'entropie de Shannon d'une liste de pics.
/// Équivalent exact du @jit(nopython=True) en Python, mais en pur Rust.
pub fn entropy_calculation(peak_intensities: &[f64]) -> f64 {
    let total_intensity: f64 = peak_intensities.iter().sum();

    if total_intensity == 0.0 {
        return 0.0;
    }

    let mut entropy = 0.0;
    for &intensity in peak_intensities {
        let prob = intensity / total_intensity;
        if prob > 0.0 {
            // Equivalent de -np.sum(probabilities * np.log2(probabilities))
            entropy -= prob * prob.log2();
        }
    }

    entropy
}