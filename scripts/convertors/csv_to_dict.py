import scripts.globals_vars
import fraghub_rust

def csv_to_dict_processing(FINAL_CSV, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    FINAL_CSV = FINAL_CSV.to_dict('records') # On garde la conversion DataFrame -> Dict ici
    return fraghub_rust.csv_to_dict_processing(
        FINAL_CSV,
        scripts.globals_vars.keys_dict,
        scripts.globals_vars.keys_list,
        progress_callback,
        total_items_callback,
        prefix_callback,
        item_type_callback
    )