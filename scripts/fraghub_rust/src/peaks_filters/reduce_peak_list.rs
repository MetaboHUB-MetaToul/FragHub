// src/peaks_filters/reduce_peak_list.rs

pub fn reduce_peak_list(
    mut peaks: Vec<(f64, f64)>,
    max_peaks: usize
) -> Vec<(f64, f64)> {
    if peaks.len() > max_peaks {
        peaks.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        peaks.truncate(max_peaks);
        peaks.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap_or(std::cmp::Ordering::Equal));
    }
    peaks
}