// src/peaks_filters/check_minimum_peak_requiered.rs

pub fn check_minimum_peak_requiered(
    peaks: Vec<(f64, f64)>,
    n_peaks: usize,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    if peaks.len() < n_peaks {
        *deletion_reason = Some("spectrum deleted because its number of peaks is below the threshold chosen by the user".to_string());
        Vec::new() // Retourne un vecteur vide pour signaler la suppression
    } else {
        peaks
    }
}