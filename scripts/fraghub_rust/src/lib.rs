use pyo3::prelude::*;

// Déclaration de vos modules
pub mod globals_vars;
pub mod loading_db;
pub mod convertors;
pub mod splash_generator; // Ajout du module splash

#[pymodule]
fn fraghub_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // --- Partie 1 : Chargement des bases de données ---
    m.add_function(wrap_pyfunction!(loading_db::load_pubchem_datas, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_ontologies_datas, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_adducts, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_keys, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_instrument_tree, m)?)?;

    // --- Partie 2 : Convertisseurs (Étape 1 de parsing_to_dict) ---
    m.add_function(wrap_pyfunction!(convertors::loaders::generate_file_hash, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_from_msp, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_from_mgf, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_json, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::loaders::load_spectrum_list_json_2, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::csv_to_dict::csv_to_dict_processing, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::json_to_dict::json_to_dict_processing, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::mgf_to_dict::mgf_to_dict_processing, m)?)?;
    m.add_function(wrap_pyfunction!(convertors::msp_to_dict::msp_to_dict_processing, m)?)?;

    // --- Partie 3 : Générateur de SPLASH ---
    m.add_function(wrap_pyfunction!(splash_generator::generate_splash_processing, m)?)?;

    Ok(())
}