// src/deletion_report.rs
use pyo3::prelude::*;
use pyo3::types::PyDict;

// On expose cette structure Rust comme une classe Python !
#[pyclass(module = "fraghub_rust")]
#[derive(Clone, Default)]
pub struct DeletionReport {
    #[pyo3(get, set)] pub duplicatas_removed: usize,
    #[pyo3(get, set)] pub previously_cleaned: usize,
    #[pyo3(get, set)] pub no_peaks_list: usize,
    #[pyo3(get, set)] pub no_smiles_no_inchi_no_inchikey: usize,
    #[pyo3(get, set)] pub no_precursor_mz: usize,
    #[pyo3(get, set)] pub low_entropy_score: usize,
    #[pyo3(get, set)] pub minimum_peaks_not_requiered: usize,
    #[pyo3(get, set)] pub all_peaks_above_precursor_mz: usize,
    #[pyo3(get, set)] pub no_peaks_in_mz_range: usize,
    #[pyo3(get, set)] pub minimum_high_peaks_not_requiered: usize,
    #[pyo3(get, set)] pub no_or_bad_adduct: usize,
}

#[pymethods]
impl DeletionReport {
    // Permet d'instancier l'objet depuis Python avec: fraghub_rust.DeletionReport()
    #[new]
    fn new() -> Self {
        Self::default() // Initialise tous les compteurs à 0
    }

    // Transforme l'objet Rust en dictionnaire Python pour la génération finale du fichier texte
    pub fn to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let dict = PyDict::new_bound(py);
        dict.set_item("duplicatas_removed", self.duplicatas_removed)?;
        dict.set_item("previously_cleaned", self.previously_cleaned)?;
        dict.set_item("no_peaks_list", self.no_peaks_list)?;
        dict.set_item("no_smiles_no_inchi_no_inchikey", self.no_smiles_no_inchi_no_inchikey)?;
        dict.set_item("no_precursor_mz", self.no_precursor_mz)?;
        dict.set_item("low_entropy_score", self.low_entropy_score)?;
        dict.set_item("minimum_peaks_not_requiered", self.minimum_peaks_not_requiered)?;
        dict.set_item("all_peaks_above_precursor_mz", self.all_peaks_above_precursor_mz)?;
        dict.set_item("no_peaks_in_mz_range", self.no_peaks_in_mz_range)?;
        dict.set_item("minimum_high_peaks_not_requiered", self.minimum_high_peaks_not_requiered)?;
        dict.set_item("no_or_bad_adduct", self.no_or_bad_adduct)?;
        Ok(dict)
    }
}