// src/deletion_report.rs

#[derive(Clone, Default, Debug)]
pub struct DeletionReport {
    pub duplicatas_removed: usize,
    pub previously_cleaned: usize,
    pub no_peaks_list: usize,
    pub no_smiles_no_inchi_no_inchikey: usize,
    pub no_precursor_mz: usize,
    pub low_entropy_score: usize,
    pub minimum_peaks_not_requiered: usize,
    pub all_peaks_above_precursor_mz: usize,
    pub no_peaks_in_mz_range: usize,
    pub minimum_high_peaks_not_requiered: usize,
    pub no_or_bad_adduct: usize,
}
