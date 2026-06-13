use pyo3::prelude::*;

// On déclare ton nouveau fichier
pub mod loading_db;

#[pymodule]
fn fraghub_rust(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // On appelle tes fonctions en passant par le module loading_db::
    m.add_function(wrap_pyfunction!(loading_db::load_pubchem_datas, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_ontologies_datas, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_adducts, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_keys, m)?)?;
    m.add_function(wrap_pyfunction!(loading_db::load_instrument_tree, m)?)?;
    Ok(())
}