import fraghub_rust
import scripts.globals_vars as g_vars

def parsing_to_dict(input_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None, step_callback=None):
    """
    Tout le parsing (JSON, MSP, CSV sans pandas, MGF) est délégué au tunnel Rust
    via la fonction parsing_to_dict_processing.
    """

    FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF = fraghub_rust.parsing_to_dict_processing(
        input_path,
        g_vars.keys_dict,
        g_vars.keys_list,
        progress_callback=progress_callback,
        total_items_callback=total_items_callback,
        prefix_callback=prefix_callback,
        item_type_callback=item_type_callback,
        step_callback=step_callback
    )

    return FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF