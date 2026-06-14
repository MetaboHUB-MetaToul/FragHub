// src/peaks_filters/check_minimum_of_high_peaks_requiered.rs

pub fn check_minimum_of_high_peaks_requiered(
    peaks: Vec<(f64, f64)>,
    intensity_percent: f64,
    no_peaks: usize,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    if peaks.is_empty() {
        return peaks;
    }

    let max_int = peaks.iter().map(|p| p.1).fold(0.0_f64, f64::max);
    let threshold = max_int * (intensity_percent / 100.0);

    let high_peaks_count = peaks.iter().filter(|&&(_, int)| int >= threshold).count();

    if high_peaks_count < no_peaks {
        *deletion_reason = Some("spectrum deleted because peaks list does not contain minimum number of high peaks required according to the value choiced by the user".to_string());
        Vec::new()
    } else {
        peaks
    }
}