// src/peaks_filters/keep_mz_in_range.rs

pub fn keep_mz_in_range(
    mut peaks: Vec<(f64, f64)>,
    mz_from: f64,
    mz_to: f64,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    peaks.retain(|&(mz, _)| mz >= mz_from && mz <= mz_to);

    if peaks.is_empty() {
        *deletion_reason = Some("spectrum deleted because peaks list is empty after removing peaks out of mz range choiced by the user".to_string());
    }

    peaks
}