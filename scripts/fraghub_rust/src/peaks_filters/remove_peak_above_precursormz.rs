// src/peaks_filters/remove_peak_above_precursormz.rs

/// Supprime les pics dont la valeur m/z est supérieure à la masse du précurseur (+ 5 Da).
/// 
/// Pour un développeur Python : On utilise la méthode `.retain()`.
/// C'est l'équivalent ultra-optimisé d'une list comprehension `[p for p in peaks if p[0] < limit]`.
/// En Rust, `.retain()` modifie le vecteur sur place (in-place) sans allouer de nouvelle mémoire.
///
/// # Arguments
/// * `peaks` - Le vecteur `mut`able de pics (la fonction s'approprie la liste et a le droit de la modifier).
/// * `precursormz` - La masse m/z du précurseur (type `f64`, un float 64-bits).
/// * `deletion_reason` - Référence mutable pour écrire la raison en cas de suppression totale.
///
/// # Returns
/// * `Vec<(f64, f64)>` : La liste des pics sans ceux au-dessus du seuil.
pub fn remove_peak_above_precursormz(
    mut peaks: Vec<(f64, f64)>,
    precursormz: f64,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    let limit = precursormz + 5.0; // En Rust, le typage est strict, on écrit 5.0 (float) et non 5 (integer).
    
    // `.retain()` garde uniquement les éléments pour lesquels la closure (fonction anonyme) renvoie `true`.
    // Le `&` dans `|&(mz, _)|` sert à déstructurer la référence vers le tuple sans la consommer.
    // L'underscore `_` ignore la seconde valeur (intensité) dont on n'a pas besoin ici.
    peaks.retain(|&(mz, _)| mz < limit);

    if peaks.is_empty() {
        *deletion_reason = Some("spectrum deleted because peaks list is empty after removing peaks above precursor m/z".to_string());
    }

    peaks // Retourne la liste filtrée.
}