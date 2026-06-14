// src/peaks_filters/remove_peak_above_precursormz.rs

pub fn remove_peak_above_precursormz(
    mut peaks: Vec<(f64, f64)>,
    precursormz: f64,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    let limit = precursormz - 5.0;
    peaks.retain(|&(mz, _)| mz < limit);

    if peaks.is_empty() {
        *deletion_reason = Some("spectrum deleted because peaks list is empty after removing peaks above precursor m/z".to_string());
    }

    peaks
}