// src/splash_generator.rs
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use sha2::{Digest, Sha256};
use std::cmp::Ordering;

const EPS_CORRECTION: f64 = 1.0e-7;
const MZ_PRECISION_FACTOR: f64 = 1_000_000.0;
const INTENSITY_PRECISION_FACTOR: f64 = 1.0;
const INTENSITY_MAP: &[u8] = b"0123456789abcdefghijklmnopqrstuvwxyz";

#[derive(Clone)]
struct Spectrum {
    peaks: Vec<(f64, f64)>, // mz, intensity
}

impl Spectrum {
    fn new(mut raw_peaks: Vec<(f64, f64)>) -> Self {
        // Normalisation (max intensity = 100.0)
        let max_int = raw_peaks.iter().map(|&(_, i)| i).fold(0.0_f64, f64::max);
        if max_int > 0.0 {
            for (_, int) in &mut raw_peaks {
                *int = (*int / max_int) * 100.0;
            }
        }
        Self { peaks: raw_peaks }
    }

    fn filter(&self, top_ions: Option<usize>, base_peak_percentage: Option<f64>) -> Self {
        let mut filtered = self.peaks.clone();

        if let Some(pct) = base_peak_percentage {
            let base_int = filtered.iter().map(|&(_, i)| i).fold(0.0_f64, f64::max);
            filtered.retain(|&(_, i)| i + EPS_CORRECTION >= pct * base_int);
        }

        if let Some(top) = top_ions {
            filtered.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal).then(a.0.partial_cmp(&b.0).unwrap_or(Ordering::Equal)));
            filtered.truncate(top);
        }

        Self { peaks: filtered }
    }
}

// Fonction utilitaire pour le hash SPLASH
fn calculate_splash(spectrum: &Spectrum) -> Option<String> {
    if spectrum.peaks.is_empty() { return None; }

    // 1. Initial Block (MS = 1)
    let initial_block = "splash10";

    // Fonction pour calculer l'histogramme
    let calc_hist = |spec: &Spectrum, base: f64, length: usize, bin_size: f64| -> String {
        let mut hist = vec![0.0; length];
        for &(mz, int) in &spec.peaks {
            let idx = (mz / bin_size) as usize % length;
            hist[idx] += int;
        }
        let max_hist = hist.iter().cloned().fold(0.0_f64, f64::max);

        let mut out = String::with_capacity(length);
        for x in hist {
            let val = (EPS_CORRECTION + (base - 1.0) * x / max_hist) as usize;
            out.push(INTENSITY_MAP[val.min(INTENSITY_MAP.len() - 1)] as char);
        }
        out
    };

    // 2. Prefilter Block (Filtered spectrum)
    let filtered_spec = spectrum.filter(Some(10), Some(0.1));
    let hist_str = calc_hist(&filtered_spec, 3.0, 10, 5.0);

    // Traduction de base 3 vers 36 pour le prefilter
    let mut n = i64::from_str_radix(&hist_str, 3).unwrap_or(0);
    let mut digits = Vec::new();
    if n == 0 { digits.push(0); }
    while n > 0 {
        digits.push((n % 36) as usize);
        n /= 36;
    }
    let mut prefilter_block = String::new();
    for &d in digits.iter().rev() {
        prefilter_block.push(INTENSITY_MAP[d] as char);
    }
    let prefilter_block = format!("{:0>4}", prefilter_block); // Remplissage avec des zéros à gauche (zfill 4)

    // 3. Similarity Block
    let similarity_block = calc_hist(spectrum, 10.0, 10, 100.0);

    // 4. Exact Hash Block
    let mut formatted_peaks: Vec<(i64, i64)> = spectrum.peaks.iter().map(|&(mz, int)| {
        (((mz + EPS_CORRECTION) * MZ_PRECISION_FACTOR) as i64, ((int + EPS_CORRECTION) * INTENSITY_PRECISION_FACTOR) as i64)
    }).collect();

    // Tri : MZ croissant, puis Intensité décroissante
    formatted_peaks.sort_by(|a, b| a.0.cmp(&b.0).then(b.1.cmp(&a.1)));

    let mut spectrum_str = String::new();
    for (i, &(mz, int)) in formatted_peaks.iter().enumerate() {
        if i > 0 { spectrum_str.push(' '); }
        spectrum_str.push_str(&format!("{}:{}", mz, int));
    }

    let mut hasher = Sha256::new();
    hasher.update(spectrum_str.as_bytes());
    let hash_result = hex::encode(hasher.finalize());
    let exact_hash = &hash_result[..20]; // Truncate à 20 caractères

    // Assemblage final
    Some(format!("{}-{}-{}-{}", initial_block, prefilter_block, similarity_block, exact_hash))
}

#[pyfunction]
#[pyo3(signature = (spectrum_list, filename, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None))]
pub fn generate_splash_processing<'py>(
    py: Python<'py>,
    spectrum_list: Bound<'py, PyList>,
    filename: String,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Bound<'py, PyList>> {

    let total = spectrum_list.len();
    if let Some(cb) = &total_items_callback { cb.call1(py, (total, 0))?; }
    if let Some(cb) = &prefix_callback { cb.call1(py, (format!("generating SPLASH for [{}]:", filename),))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("spectra",))?; }

    // Extraction des spectres depuis Python vers des structs Rust pour le multithreading
    struct PySpectrum {
        index: usize,
        peaks: Vec<(f64, f64)>,
    }

    let mut rust_spectra = Vec::with_capacity(total);
    for (i, item) in spectrum_list.iter().enumerate() {
        if let Ok(dict) = item.downcast::<PyDict>() {
            if let Ok(Some(peaks_list)) = dict.get_item("PEAKS_LIST") {
                if let Ok(extracted_peaks) = peaks_list.extract::<Vec<Vec<f64>>>() {
                    let peaks: Vec<(f64, f64)> = extracted_peaks.into_iter().filter_map(|p| {
                        if p.len() >= 2 { Some((p[0], p[1])) } else { None }
                    }).collect();
                    rust_spectra.push(PySpectrum { index: i, peaks });
                }
            }
        }
    }

    // MULTITHREADING RAYON : Calcul des Splashs en parallèle
    let splash_results: Vec<(usize, Option<String>)> = rust_spectra
        .into_par_iter()
        .map(|spec| {
            let spectrum_obj = Spectrum::new(spec.peaks);
            let splash = calculate_splash(&spectrum_obj);
            (spec.index, splash)
        })
        .collect();

    // RETOUR À PYTHON : Mise à jour des dictionnaires
    let mut processed = 0;
    for (index, splash_opt) in splash_results {
        if let Some(splash_str) = splash_opt {
            if let Ok(dict) = spectrum_list.get_item(index).unwrap().downcast::<PyDict>() {
                dict.set_item("SPLASH", splash_str)?;
            }
        }
        processed += 1;
        if processed % 500 == 0 || processed == total {
            if let Some(cb) = &progress_callback { cb.call1(py, (processed,))?; }
        }
    }

    Ok(spectrum_list)
}