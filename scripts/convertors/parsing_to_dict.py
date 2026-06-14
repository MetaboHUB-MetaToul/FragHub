from scripts.convertors.json_to_dict import *
from scripts.convertors.msp_to_dict import *
from scripts.convertors.csv_to_dict import *
from scripts.convertors.mgf_to_dict import *
from scripts.convertors.loaders import *
import pandas as pd
import hashlib
import time
import json
import os
import re

def generate_file_hash(file_path):
    try:
        file_size = os.path.getsize(file_path)
        data_to_hash = str(file_size)
        sha256_hash = hashlib.sha256(data_to_hash.encode('utf-8')).hexdigest()
        return sha256_hash
    except FileNotFoundError:
        return f"Error: File not found at {file_path}"

def detect_separator(file_path):
    try:
        with open(file_path, 'r', encoding='UTF-8') as f:
            first_line = f.readline()
            if not first_line:
                return ';'
            tab_count = first_line.count('\t')
            semicolon_count = first_line.count(';')
            if tab_count > semicolon_count:
                return '\t'
            return ';'
    except Exception:
        return ';'

def concatenate_csv(csv_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    total_files = len(csv_list)
    if total_items_callback: total_items_callback(total_files, 0)
    if prefix_callback: prefix_callback("Reading CSV files:")
    if item_type_callback: item_type_callback("csv_files")

    df_list = []
    processed_files = 0

    for file in csv_list:
        file_hash = generate_file_hash(file)
        separator = detect_separator(file)
        df = pd.read_csv(file, sep=separator, quotechar='"', encoding="UTF-8", dtype=str)
        df.columns = df.columns.str.lower()

        if 'filename' not in df.columns:
            df['filename'] = os.path.basename(file)
        if 'filehash' not in df.columns:
            df['filehash'] = file_hash

        df.columns = df.columns.str.lower()
        df = df.astype(str)
        df_list.append(df)

        processed_files += 1
        if progress_callback: progress_callback(processed_files)

    df = pd.concat(df_list, ignore_index=True)
    return df

def concatenate_MGF(mgf_list, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    spectrum_list = []
    for files in mgf_list:
        spectrum_list.extend(load_spectrum_list_from_mgf(files, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback))
    return spectrum_list

def parsing_to_dict(input_path, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None, step_callback=None):

    # ======================================================
    # JSON PROCESSING
    # ======================================================
    FINAL_JSON = []
    json_list = [f for f in input_path if f.endswith(".json")]

    if json_list:
        time.sleep(0.01)
        if step_callback: step_callback("-- PARSING JSON TO DICT --")
        time.sleep(0.01)

        for json_file in json_list:
            try:
                raw_json_tunnel = load_spectrum_list_json(json_file, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            except Exception as e:
                print(f"Fallback au chargeur JSONL pour {json_file} : {e}")
                raw_json_tunnel = load_spectrum_list_json_2(json_file, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

            dict_list = json_to_dict_processing(raw_json_tunnel, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

            # Assignation directe pour éviter le freeze de `.extend()`
            if not FINAL_JSON:
                FINAL_JSON = dict_list
            else:
                FINAL_JSON.extend(dict_list)
            del dict_list

    # ======================================================
    # MSP PROCESSING
    # ======================================================
    FINAL_MSP = []
    msp_list = [f for f in input_path if f.endswith(".msp")]

    if msp_list:
        time.sleep(0.01)
        if step_callback: step_callback("-- PARSING MSP TO DICT --")
        time.sleep(0.01)

        for msp_file in msp_list:
            raw_msp_tunnel = load_spectrum_list_from_msp(msp_file, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            dict_list = msp_to_dict_processing(raw_msp_tunnel, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

            if not FINAL_MSP:
                FINAL_MSP = dict_list
            else:
                FINAL_MSP.extend(dict_list)
            del dict_list

    # ======================================================
    # MGF PROCESSING
    # ======================================================
    FINAL_MGF = []
    mgf_list = [f for f in input_path if f.endswith(".mgf")]
    if mgf_list:
        time.sleep(0.01)
        if step_callback: step_callback("-- PARSING MGF TO DICT --")
        time.sleep(0.01)
        FINAL_MGF = concatenate_MGF(mgf_list, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        FINAL_MGF = mgf_to_dict_processing(FINAL_MGF, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

    # ======================================================
    # CSV PROCESSING
    # ======================================================
    FINAL_CSV = []
    csv_list = [f for f in input_path if f.endswith(".csv")]
    if csv_list:
        time.sleep(0.01)
        if step_callback: step_callback("-- PARSING CSV TO DICT --")
        time.sleep(0.01)
        FINAL_CSV = concatenate_csv(csv_list, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        FINAL_CSV = csv_to_dict_processing(FINAL_CSV, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

    return FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF