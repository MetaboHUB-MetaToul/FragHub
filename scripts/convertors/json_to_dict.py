import scripts.globals_vars
import fraghub_rust
import gc
import time

def json_to_dict_processing(FINAL_JSON, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    gc.disable()
    try:
        return fraghub_rust.json_to_dict_processing(
            FINAL_JSON,
            scripts.globals_vars.keys_dict,
            scripts.globals_vars.keys_list,
            progress_callback,
            total_items_callback,
            prefix_callback,
            item_type_callback
        )
    finally:
        # On affiche la barre de chargement indéterminée (total = 0)
        if total_items_callback: total_items_callback(0)
        if prefix_callback: prefix_callback("Consolidating memory (Garbage Collection)...")
        time.sleep(0.1) # Laisse le temps à Vue.js d'animer la transition

        gc.enable()