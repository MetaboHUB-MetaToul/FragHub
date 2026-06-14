import scripts.deletion_report
import fraghub_rust
import pandas as pd
import os

def remove_duplicatas(spectrum_list, output_directory, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Supprime les spectres dupliqués (SPLASH + INCHIKEY) via Rust et exporte les supprimés.
    Sert de "pont" automatique entre le DataFrame de MAIN.py et la liste native de Rust.
    """
    # 1. On récupère automatiquement l'ordre des colonnes depuis le DataFrame
    ordered_columns = list(spectrum_list.columns)

    # 2. On convertit le DataFrame en liste de dictionnaires (Ce que Rust attend !)
    dict_list = spectrum_list.to_dict(orient='records')

    # 3. On délègue le travail lourd à Rust
    dict_list, deleted_count = fraghub_rust.remove_duplicatas_processing(
        dict_list,
        output_directory,
        ordered_columns,
        progress_callback=progress_callback,
        total_items_callback=total_items_callback,
        prefix_callback=prefix_callback,
        item_type_callback=item_type_callback
    )

    # 4. On met à jour le rapport global des suppressions
    scripts.deletion_report.duplicatas_removed = deleted_count

    # On renvoie la liste filtrée
    return dict_list