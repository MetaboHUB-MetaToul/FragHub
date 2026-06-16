// src/lib.rs
use pyo3::prelude::*;

// Déclaration de vos modules
pub mod globals_vars;
pub mod global_state;
pub mod loading_db;
pub mod convertors;
pub mod splash_generator;
pub mod duplicatas_remover;
pub mod update_checker;
pub mod normalizer;
pub mod peaks_filters;
pub mod spectrum_cleaning;
pub mod complete_from_pubchem_datas;
pub mod ontologies_completion;
pub mod de_novo_calculation;
pub mod normalize_to_not_found;
pub mod splitter;
pub mod csv_to_msp;
pub mod writers;
pub mod report;
pub mod set_projects;
pub mod deletion_report;
pub mod rdkit_bridge;
pub mod main_orchestrator;

#[pymodule]
fn fraghub_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // --- Orchestrator ---
    m.add_function(wrap_pyfunction!(main_orchestrator::main_orchestrator, m)?)?;

    // --- Partie 1 : Chargement des bases de données ---
    m.add_function(wrap_pyfunction!(loading_db::load_internal_databases, m)?)?;

    // --- Partie 2 : Convertisseurs ---
    m.add_function(wrap_pyfunction!(convertors::loaders::generate_file_hash, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_from_msp, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_from_mgf, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_json, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_json_2, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::csv_to_dict::load_and_parse_csv, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::json_to_dict::json_to_dict_processing, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::mgf_to_dict::mgf_to_dict_processing, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::msp_to_dict::msp_to_dict_processing, m)?)?;

    // --- Partie 3 : Traitements de masse ---
    m.add_function(wrap_pyfunction!(splash_generator::generate_splash_processing, m)?)?;
    m.add_function(wrap_pyfunction!(duplicatas_remover::remove_duplicatas_processing, m)?)?;
    m.add_function(wrap_pyfunction!(update_checker::check_for_update_processing, m)?)?;
    m.add_function(wrap_pyfunction!(spectrum_cleaning::spectrum_cleaning_processing, m)?)?;
    m.add_function(wrap_pyfunction!(complete_from_pubchem_datas::complete_from_pubchem_datas, m)?)?;
    m.add_function(wrap_pyfunction!(ontologies_completion::ontologies_completion_processing, m)?)?;
    m.add_function(wrap_pyfunction!(de_novo_calculation::de_novo_calculation_processing, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_to_not_found::normalize_to_not_found_processing, m)?)?;

    // --- Les oublis sont rajoutés ici ! ---
    m.add_function(wrap_pyfunction!(splitter::split_pos_neg, m)?)?;
    m.add_function(wrap_pyfunction!(splitter::split_LC_GC, m)?)?;
    m.add_function(wrap_pyfunction!(splitter::exp_in_silico_splitter, m)?)?;

    m.add_function(wrap_pyfunction!(csv_to_msp::csv_to_msp_processing, m)?)?;

    m.add_function(wrap_pyfunction!(writers::writting_msp_processing, m)?)?;
    m.add_function(wrap_pyfunction!(writers::writting_csv_processing, m)?)?;
    m.add_function(wrap_pyfunction!(writers::writting_json_processing, m)?)?;

    m.add_function(wrap_pyfunction!(convertors::parsing_to_dict::parsing_to_dict_processing, m)?)?;

    m.add_function(wrap_pyfunction!(report::generate_report_processing, m)?)?;

    m.add_function(wrap_pyfunction!(set_projects::reset_updates, m)?)?;
    m.add_function(wrap_pyfunction!(set_projects::init_project, m)?)?;

    m.add_class::<deletion_report::DeletionReport>()?;

    m.add_function(wrap_pyfunction!(rdkit_bridge::process_mols, m)?)?;

    Ok(())
}