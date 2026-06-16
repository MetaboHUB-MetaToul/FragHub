// src/csv_to_msp.rs
use pyo3::prelude::*;
use rayon::prelude::*;
use crate::spectrum::Spectrum;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::fmt::Write; // <-- Indispensable pour la macro write!

// Fonction pour extraire et nettoyer une valeur depuis le dictionnaire Python
fn get_string(spec: &Spectrum, key: &str) -> String {
    if key == "PEAKS_LIST" {
        if spec.peaks.is_empty() { return "NOT FOUND".to_string(); }
        let mut peaks_str = String::with_capacity(spec.peaks.len() * 20);
        for (i, &(mz, int)) in spec.peaks.iter().enumerate() {
            if i > 0 { peaks_str.push('\n'); }
            peaks_str.push_str(&format!("{} {}", mz, int));
        }
        return peaks_str;
    }
    if let Some(val) = spec.metadata.get(key) {
        let trimmed = val.trim();
        if trimmed.is_empty() || trimmed.eq_ignore_ascii_case("nan") {
            return "NOT FOUND".to_string();
        }
        return val.clone();
    }
    "NOT FOUND".to_string()
}

#[allow(clippy::too_many_arguments)]
pub fn csv_to_msp_processing(
    py: Python,
    pos_lc_df: Vec<Spectrum>,
    pos_lc_df_insilico: Vec<Spectrum>,
    pos_gc_df: Vec<Spectrum>,
    pos_gc_df_insilico: Vec<Spectrum>,
    neg_lc_df: Vec<Spectrum>,
    neg_lc_df_insilico: Vec<Spectrum>,
    neg_gc_df: Vec<Spectrum>,
    neg_gc_df_insilico: Vec<Spectrum>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<(Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>, Vec<String>)> {

    // On rassemble toutes les catégories pour les traiter d'un seul coup
    let tasks = vec![
        pos_lc_df, pos_lc_df_insilico, pos_gc_df, pos_gc_df_insilico,
        neg_lc_df, neg_lc_df_insilico, neg_gc_df, neg_gc_df_insilico
    ];

    let total_items: usize = tasks.iter().map(|l| l.len()).sum();

    // UI Globale : Une seule barre pour toutes les conversions confondues
    if let Some(cb) = &prefix_callback { cb.call1(py, ("Converting all CSV to MSP (Multithreaded):",))?; }
    if let Some(cb) = &item_type_callback { cb.call1(py, ("rows",))?; }
    if let Some(cb) = &total_items_callback { cb.call1(py, (total_items, 0))?; }

    if total_items == 0 {
        return Ok((Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new()));
    }

    let global_processed = Arc::new(AtomicUsize::new(0));
    let progress_cb = progress_callback.clone();

    // 100% MULTITHREAD : On libère le GIL Python
    let results: Result<Vec<Vec<String>>, PyErr> = py.allow_threads(|| {

        // Rayon traite les 8 listes en parallèle (into_par_iter)
        let res: Vec<Vec<String>> = tasks.into_par_iter().map(|data_list| {
            if data_list.is_empty() {
                return Vec::new();
            }

            let mut spectrum_list = Vec::with_capacity(data_list.len());
            let chunk_size = 2500;

            // Découpage en lots à l'intérieur de chaque liste pour mettre à jour l'interface proprement
            for chunk in data_list.chunks(chunk_size) {

                // Sous-parallélisation de Rayon : Construction des chaînes de caractères sur tous les CPU dispo
                let chunk_results: Vec<String> = chunk.par_iter().map(|spec| {

                    // Optimisation Mémoire : On alloue un seul bloc assez grand (2048 octets)
                    let mut spectrum = String::with_capacity(2048);

                    // Optimisation Vitesse : On écrit directement dans le bloc sans créer de variables temporaires
                    let _ = write!(
                        &mut spectrum,
                        "NAME: {}\nPRECURSORMZ: {}\nPRECURSORTYPE: {}\nFORMULA: {}\nINCHIKEY: {}\nINCHI: {}\nSMILES: {}\nRT: {}\nIONMODE: {}\nINSTRUMENTTYPE: {}\nINSTRUMENT: {}\nCOLLISIONENERGY: {}\nEXACTMASS: {}\nIONIZATION: {}\nMSLEVEL: {}\nCOMMENT: FILENAME={}; FILEHASH={}; PREDICTED={}; SPLASH={}; SPECTRUMID={}; RESOLUTION={}; SYNON={}; FRAGMENTATIONMODE={}; AVERAGEMASS={}; ENTROPY={}; ONTOLOGIES = \"CLASSYFIRE_SUPERCLASS={}, CLASSYFIRE_CLASS = {}, CLASSYFIRE_SUBCLASS = {}, NPCLASS_PATHWAY = {}, NPCLASS_SUPERCLASS = {}, NPCLASS_CLASS = {}\"\nNUM PEAKS: {}\n",
                        get_string(spec, "NAME"),
                        get_string(spec, "PRECURSORMZ"),
                        get_string(spec, "PRECURSORTYPE"),
                        get_string(spec, "FORMULA"),
                        get_string(spec, "INCHIKEY"),
                        get_string(spec, "INCHI"),
                        get_string(spec, "SMILES"),
                        get_string(spec, "RT"),
                        get_string(spec, "IONMODE"),
                        get_string(spec, "INSTRUMENTTYPE"),
                        get_string(spec, "INSTRUMENT"),
                        get_string(spec, "COLLISIONENERGY"),
                        get_string(spec, "EXACTMASS"),
                        get_string(spec, "IONIZATION"),
                        get_string(spec, "MSLEVEL"),
                        // Début des variables du commentaire
                        get_string(spec, "FILENAME"), get_string(spec, "FILEHASH"), get_string(spec, "PREDICTED"),
                        get_string(spec, "SPLASH"), get_string(spec, "SPECTRUMID"), get_string(spec, "RESOLUTION"),
                        get_string(spec, "SYNON"), get_string(spec, "FRAGMENTATIONMODE"), get_string(spec, "AVERAGEMASS"),
                        get_string(spec, "ENTROPY"), get_string(spec, "CLASSYFIRE_SUPERCLASS"), get_string(spec, "CLASSYFIRE_CLASS"),
                        get_string(spec, "CLASSYFIRE_SUBCLASS"), get_string(spec, "NPCLASS_PATHWAY"), get_string(spec, "NPCLASS_SUPERCLASS"),
                        get_string(spec, "NPCLASS_CLASS"),
                        // Fin des variables du commentaire
                        get_string(spec, "NUM PEAKS")
                    );

                    let peaks = get_string(spec, "PEAKS_LIST");
                    if peaks != "NOT FOUND" { spectrum.push_str(&peaks); }
                    spectrum.push('\n');

                    spectrum
                }).collect();

                spectrum_list.extend(chunk_results);

                // Mise à jour de l'UI (GIL récupéré de façon sécurisée et ponctuelle)
                let current = global_processed.fetch_add(chunk.len(), Ordering::Relaxed) + chunk.len();
                if let Some(ref cb) = progress_cb {
                    Python::with_gil(|py| { let _ = cb.call1(py, (current,)); });
                }
            }
            spectrum_list
        }).collect();

        Ok(res)
    });

    // Récupération des vecteurs générés
    let mut final_lists = results?;

    // On dépile dans l'ordre inverse exact de notre vecteur `tasks` initial
    let neg_gc_in = final_lists.pop().unwrap();
    let neg_gc = final_lists.pop().unwrap();
    let neg_lc_in = final_lists.pop().unwrap();
    let neg_lc = final_lists.pop().unwrap();
    let pos_gc_in = final_lists.pop().unwrap();
    let pos_gc = final_lists.pop().unwrap();
    let pos_lc_in = final_lists.pop().unwrap();
    let pos_lc = final_lists.pop().unwrap();

    // Sécurité 100% de la barre UI
    if let Some(cb) = &progress_callback { cb.call1(py, (total_items,))?; }

    Ok((pos_lc, pos_lc_in, pos_gc, pos_gc_in, neg_lc, neg_lc_in, neg_gc, neg_gc_in))
}