import scripts.globals_vars
import fraghub_rust

def mgf_to_dict_processing(FINAL_MGF, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    return fraghub_rust.mgf_to_dict_processing(
        FINAL_MGF,
        scripts.globals_vars.keys_dict,
        scripts.globals_vars.keys_list,
        progress_callback,
        total_items_callback,
        prefix_callback,
        item_type_callback
    )