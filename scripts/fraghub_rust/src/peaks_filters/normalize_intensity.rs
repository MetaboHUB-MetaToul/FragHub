// src/peaks_filters/normalize_intensity.rs

pub fn normalize_intensity(mut peaks: Vec<(f64, f64)>) -> Vec<(f64, f64)> {
    if peaks.is_empty() {
        return peaks;
    }

    let max_int = peaks.iter().map(|p| p.1).fold(0.0_f64, f64::max);

    if max_int != 0.0 {
        for p in &mut peaks {
            p.1 /= max_int;
        }
        peaks
    } else {
        Vec::new()
    }
}