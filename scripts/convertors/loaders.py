import fraghub_rust

def generate_file_hash(file_path):
    """
    Appel direct au générateur de hash ultra-rapide en Rust.
    """
    return fraghub_rust.generate_file_hash(file_path)

def load_spectrum_list_from_msp(msp_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Redirection vers le chargeur MSP natif Rust.
    """
    return fraghub_rust.load_spectrum_list_from_msp(
        msp_file_path, progress_callback, total_items_callback, prefix_callback, item_type_callback
    )

def load_spectrum_list_from_mgf(mgf_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Redirection vers le chargeur MGF natif Rust.
    """
    return fraghub_rust.load_spectrum_list_from_mgf(
        mgf_file_path, progress_callback, total_items_callback, prefix_callback, item_type_callback
    )

def load_spectrum_list_json(json_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Redirection vers le Streamer natif Rust pour les gros JSON (équivalent ijson).
    Retourne l'itérateur Rust JsonSpectrumStreamer.
    """
    return fraghub_rust.load_spectrum_list_json(
        json_file_path, progress_callback, total_items_callback, prefix_callback, item_type_callback
    )

def load_spectrum_list_json_2(json_file_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Redirection vers le Streamer natif Rust pour le format JSONL (Ligne par Ligne).
    Retourne l'itérateur Rust JsonLinesStreamer.
    """
    return fraghub_rust.load_spectrum_list_json_2(
        json_file_path, progress_callback, total_items_callback, prefix_callback, item_type_callback
    )