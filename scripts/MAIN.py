import fraghub_rust

def MAIN(parameters_dict, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None, step_callback=None, completion_callback=None, deletion_callback=None, stop_flag=None):
    try:
        fraghub_rust.main_orchestrator(
            parameters_dict,
            progress_callback,
            total_items_callback,
            prefix_callback,
            item_type_callback,
            step_callback,
            completion_callback,
            deletion_callback,
            stop_flag
        )
    except Exception as e:
        if str(e) == "Process stopped by user.":
            if deletion_callback:
                deletion_callback("\n-- PROCESS INTERRUPTED BY USER --")
        else:
            raise e
