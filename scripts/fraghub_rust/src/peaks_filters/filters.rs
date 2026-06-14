// src/peaks_filters/filters.rs
use std::collections::HashMap;

// Filtre obligatoire inclus directement ici (comme dans votre Python d'origine)
pub fn remove_non_positive_peaks(mut peaks: Vec<(f64, f64)>) -> Vec<(f64, f64)> {
    peaks.retain(|&(_, int)| int > 0.0);
    peaks
}

pub fn apply_filters(
    mut peaks: Vec<(f64, f64)>,
    precursormz: Option<f64>,
    parameters: &HashMap<String, f64>,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {

    // --- Step 1: Mandatory filter ---
    peaks = remove_non_positive_peaks(peaks);

    // --- Filter 1: Check minimum required peak count ---
    if parameters.get("check_minimum_peak_requiered").copied().unwrap_or(0.0) == 1.0 {
        let n_peaks = parameters.get("check_minimum_peak_requiered_n_peaks").copied().unwrap_or(0.0) as usize;
        peaks = super::check_minimum_peak_requiered::check_minimum_peak_requiered(peaks, n_peaks, deletion_reason);
        if peaks.is_empty() { return peaks; }
    }

    // --- Filter 2: Remove peaks above precursor m/z ---
    if parameters.get("remove_peak_above_precursormz").copied().unwrap_or(0.0) == 1.0 {
        if let Some(pmz) = precursormz {
            peaks = super::remove_peak_above_precursormz::remove_peak_above_precursormz(peaks, pmz, deletion_reason);
            if peaks.is_empty() { return peaks; }
        }
    }

    // --- Filter 3: Reduce peak list to a maximum number of peaks ---
    if parameters.get("reduce_peak_list").copied().unwrap_or(0.0) == 1.0 {
        let max_peaks = parameters.get("reduce_peak_list_max_peaks").copied().unwrap_or(0.0) as usize;
        peaks = super::reduce_peak_list::reduce_peak_list(peaks, max_peaks);
    }

    // --- Filter 4: Normalize peak intensity ---
    if parameters.get("normalize_intensity").copied().unwrap_or(0.0) == 1.0 {
        peaks = super::normalize_intensity::normalize_intensity(peaks);
        if peaks.is_empty() { return peaks; }
    }

    // --- Filter 5: Keep peaks within a user-defined m/z range ---
    if parameters.get("keep_mz_in_range").copied().unwrap_or(0.0) == 1.0 {
        let mz_from = parameters.get("keep_mz_in_range_from_mz").copied().unwrap_or(0.0);
        let mz_to = parameters.get("keep_mz_in_range_to_mz").copied().unwrap_or(0.0);
        peaks = super::keep_mz_in_range::keep_mz_in_range(peaks, mz_from, mz_to, deletion_reason);
        if peaks.is_empty() { return peaks; }
    }

    // --- Filter 6: Check minimum number of high-intensity peaks ---
    if parameters.get("check_minimum_of_high_peaks_requiered").copied().unwrap_or(0.0) == 1.0 {
        let intensity_percent = parameters.get("check_minimum_of_high_peaks_requiered_intensity_percent").copied().unwrap_or(0.0);
        let no_peaks = parameters.get("check_minimum_of_high_peaks_requiered_no_peaks").copied().unwrap_or(0.0) as usize;
        peaks = super::check_minimum_of_high_peaks_requiered::check_minimum_of_high_peaks_requiered(peaks, intensity_percent, no_peaks, deletion_reason);
        if peaks.is_empty() { return peaks; }
    }

    peaks
}