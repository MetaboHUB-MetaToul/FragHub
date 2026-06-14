// src/normalizer/mod.rs
use std::collections::HashMap;
use serde_json::Value;

pub struct NormalizerContext {
    pub adduct_pos: HashMap<String, String>,
    pub adduct_neg: HashMap<String, String>,
    pub adduct_massdiff_pos: HashMap<String, f64>,
    pub adduct_massdiff_neg: HashMap<String, f64>,
    pub instrument_tree: Value,
}

pub mod values_normalizer;
pub mod normalize_empties;
pub mod repair_mol_descriptors;
pub mod delete_no_smiles_no_inchi;
pub mod normalize_ionization;
pub mod normalize_instruments_and_resolution;
pub mod normalize_adduct;
pub mod normalize_ionmode;
pub mod normalize_predicted; // <-- NOUVEAU
pub mod normalize_ms_level; // <-- NOUVEAU
pub mod normalize_retentiontime; // <-- NOUVEAU
pub mod missing_precursormz_re_calculation;
pub mod check_for_bad_adduct;