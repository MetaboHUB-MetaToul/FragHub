// src/peaks_filters/keep_mz_in_range.rs

/// Supprime les pics qui tombent en dehors de la plage m/z [mz_from, mz_to].
///
/// # Arguments
/// * `peaks` (Vec<(f64, f64)>) : Le vecteur `mut`able de pics.
/// * `mz_from` (f64) : Borne inférieure de la masse m/z.
/// * `mz_to` (f64) : Borne supérieure de la masse m/z.
/// * `deletion_reason` (&mut Option<String>) : Référence mutable pour tracker la suppression.
///
/// # Returns
/// * `Vec<(f64, f64)>` : La liste filtrée (vide si tous les pics sont supprimés).
pub fn keep_mz_in_range(
    mut peaks: Vec<(f64, f64)>,
    mz_from: f64,
    mz_to: f64,
    deletion_reason: &mut Option<String>
) -> Vec<(f64, f64)> {
    // Comme pour `remove_peak_above_precursormz`, `.retain()` modifie le vecteur sur place.
    // La condition `mz >= mz_from && mz <= mz_to` est conservée (`true`), le reste est jeté.
    peaks.retain(|&(mz, _)| mz >= mz_from && mz <= mz_to);

    if peaks.is_empty() {
        *deletion_reason = Some("spectrum deleted because peaks list is empty after removing peaks out of mz range choiced by the user".to_string());
    }

    peaks
}