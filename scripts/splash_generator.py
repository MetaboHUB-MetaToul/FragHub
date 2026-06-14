import os
import fraghub_rust

def process_converted_after(spectrum_list, mode, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Process converted spectrum list after conversion using Rust.
    """
    if mode == "MSP":
        filename = "MSP_converted.json"
    elif mode == "XML":
        filename = "XML_converted.json"
    elif mode == "CSV":
        filename = "CSV_converted.json"
    elif mode == "JSON":
        filename = "JSON_converted.json"
    elif mode == "MGF":
        filename = "MGF_converted.json"
    else:
        filename = "Unknown"

    filename = filename.split("_")[0]

    # Appel direct à Rust qui fait le multithreading, le calcul et met à jour le dictionnaire
    spectrum_list = fraghub_rust.generate_splash_processing(
        spectrum_list,
        filename,
        progress_callback=progress_callback,
        total_items_callback=total_items_callback,
        prefix_callback=prefix_callback,
        item_type_callback=item_type_callback
    )

    return spectrum_list

def generate_splash_id(FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    if FINAL_MSP:
        FINAL_MSP = process_converted_after(FINAL_MSP, "MSP", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

    if FINAL_CSV:
        FINAL_CSV = process_converted_after(FINAL_CSV, "CSV", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

    if FINAL_JSON:
        FINAL_JSON = process_converted_after(FINAL_JSON, "JSON", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

    if FINAL_MGF:
        FINAL_MGF = process_converted_after(FINAL_MGF, "MGF", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

    return FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF