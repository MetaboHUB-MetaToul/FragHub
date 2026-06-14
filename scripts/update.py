import scripts.deletion_report
import fraghub_rust

def check_for_update_processing(spectrum_list, output_directory, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Vérifie les mises à jour via Rust.
    """
    if not spectrum_list:
        return spectrum_list, False

    # On récupère automatiquement les colonnes depuis le premier dictionnaire
    ordered_columns = list(spectrum_list[0].keys())

    # Délégation à Rust !
    final_spectrum_list, update, deleted_count = fraghub_rust.check_for_update_processing(
        spectrum_list,
        output_directory,
        ordered_columns,
        progress_callback=progress_callback,
        total_items_callback=total_items_callback,
        prefix_callback=prefix_callback,
        item_type_callback=item_type_callback
    )

    # Mise à jour du rapport
    scripts.deletion_report.previously_cleaned = deleted_count

    return final_spectrum_list, update