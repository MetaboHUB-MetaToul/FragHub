from scripts.set_projects import parameters_dict
import pandas as pd
import numpy as np
import json
import time
import os
import re


def write_msp(spectrum_list, filename, mode, update, output_directory, progress_callback=None,
              total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Writes a list of mass spectrometry spectra (as strings) to an MSP format file.

    :param spectrum_list: A list of spectrum strings to be written.
    :type spectrum_list: list
    :param filename: The name of the output MSP file (e.g., "POS_LC.msp").
    :type filename: str
    :param mode: The ionization mode ('POS' or 'NEG'), used for directory path construction.
    :type mode: str
    :param update: If True, data is appended to the existing file; otherwise, the file is overwritten.
    :type update: bool
    :param output_directory: The base output directory path.
    :type output_directory: str
    :param progress_callback: Function to report item-by-item progress. (Optional)
    :type progress_callback: callable or None
    :param total_items_callback: Function to set the total number of items to process. (Optional)
    :type total_items_callback: callable or None
    :param prefix_callback: Function to set the prefix for the current task. (Optional)
    :type prefix_callback: callable or None
    :param item_type_callback: Function to specify the type of items being processed. (Optional)
    :type item_type_callback: callable or None
    :return: None
    """

    # Construct the output file path: {output_directory}/MSP/{mode}/{filename}
    output_file_path = f"{output_directory}/MSP/{mode}/{filename}"

    # Set the context/task description
    if prefix_callback:
        prefix_callback(f"Writing {filename} to MSP:")

    # Indicate the type of elements being processed
    if item_type_callback:
        item_type_callback("spectra")

    # Initialize the total number of items for progress tracking
    total_spectra = len(spectrum_list)
    if total_items_callback:
        total_items_callback(total_spectra, 0)

    # Determine file mode ('a' for append, 'w' for write/overwrite)
    file_mode = 'a' if update else 'w'

    # Open the file for writing
    with open(output_file_path, file_mode, encoding="UTF-8") as f:
        # Iterate through each spectrum string in the list
        for index, spectrum in enumerate(spectrum_list):
            try:
                # Write the spectrum block and an extra line break for separation
                f.write(spectrum)
                f.write("\n\n")

                # Update the progress after successful write
                if progress_callback:
                    progress_callback(index + 1)
            except Exception as e:
                # Log or handle the error, but continue processing the rest of the list
                # Removed print statement as per user request to remove all prints
                continue


def writting_msp(POS_LC, POS_LC_insilico, POS_GC, POS_GC_insilico, NEG_LC, NEG_LC_insilico, NEG_GC, NEG_GC_insilico,
                 output_directory, update=False, progress_callback=None, total_items_callback=None,
                 prefix_callback=None, item_type_callback=None):
    """
    Orchestrates the writing of all structured spectral lists (LC/GC, observed/in-silico, POS/NEG)
    to their respective MSP files using `write_msp`.

    Memory is explicitly managed by deleting each list after it has been written.

    :param POS_LC: List of Positive LC spectra.
    :param POS_LC_insilico: List of Positive LC in-silico spectra.
    :param POS_GC: List of Positive GC spectra.
    :param POS_GC_insilico: List of Positive GC in-silico spectra.
    :param NEG_LC: List of Negative LC spectra.
    :param NEG_LC_insilico: List of Negative LC in-silico spectra.
    :param NEG_GC: List of Negative GC spectra.
    :param NEG_GC_insilico: List of Negative GC in-silico spectra.
    :param output_directory: The base directory for output.
    :type output_directory: str
    :param update: Flag indicating whether to append to or overwrite files (default is overwrite).
    :type update: bool
    :return: None
    """

    time.sleep(0.1)
    write_msp(POS_LC, "POS_LC.msp", "POS", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del POS_LC
    time.sleep(0.1)
    write_msp(POS_LC_insilico, "POS_LC_insilico.msp", "POS", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del POS_LC_insilico
    time.sleep(0.1)
    write_msp(POS_GC, "POS_GC.msp", "POS", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del POS_GC
    time.sleep(0.1)
    write_msp(POS_GC_insilico, "POS_GC_insilico.msp", "POS", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del POS_GC_insilico
    time.sleep(0.1)
    write_msp(NEG_LC, "NEG_LC.msp", "NEG", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del NEG_LC
    time.sleep(0.1)
    write_msp(NEG_LC_insilico, "NEG_LC_insilico.msp", "NEG", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del NEG_LC_insilico
    time.sleep(0.1)
    write_msp(NEG_GC, "NEG_GC.msp", "NEG", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del NEG_GC
    time.sleep(0.1)
    write_msp(NEG_GC_insilico, "NEG_GC_insilico.msp", "NEG", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del NEG_GC_insilico


def write_csv(df, filename, mode, update, output_directory, progress_callback=None, total_items_callback=None,
              prefix_callback=None, item_type_callback=None):
    """
    Writes a pandas DataFrame to a tab-separated CSV file in chunks for memory efficiency.
    The 'PEAKS_LIST' column is pre-processed to replace newlines with semicolons.

    :param df: The DataFrame to be written.
    :type df: pd.DataFrame
    :param filename: The name of the output CSV file.
    :type filename: str
    :param mode: The ionization mode ('POS' or 'NEG'), used for directory path construction.
    :type mode: str
    :param update: If True, appends data without headers; otherwise, overwrites and writes headers.
    :type update: bool
    :param output_directory: The base output directory path.
    :type output_directory: str
    :param progress_callback: Function to track progress of row writing. (Optional)
    :type progress_callback: callable or None
    :param total_items_callback: Function to set the total number of rows. (Optional)
    :type total_items_callback: callable or None
    :param prefix_callback: Function to indicate the current task's description context. (Optional)
    :type prefix_callback: callable or None
    :param item_type_callback: Function to indicate the type of elements being processed. (Optional)
    :type item_type_callback: callable or None
    :return: None.
    """
    # Replace newline characters with semicolons in the PEAKS_LIST column for single-line storage
    if 'PEAKS_LIST' in df.columns:
        df['PEAKS_LIST'] = df['PEAKS_LIST'].str.replace('\n', ';', regex=False)

    # Construct the file path dynamically
    output_file_path = f"{output_directory}/CSV/{mode}/{filename}"

    # Define chunk size for writing DataFrame in parts
    chunk_size = 5000

    # Calculate the total number of chunks (not explicitly used but defined)
    num_chunks = int(np.ceil(df.shape[0] / chunk_size))

    # Set up task description
    if prefix_callback:
        prefix_callback(f"Writing {filename} to CSV:")

    # Indicate item type
    if item_type_callback:
        item_type_callback("rows")

    # Define total items expected
    total_rows = len(df)
    if total_items_callback:
        total_items_callback(total_rows, 0)

    # Process the DataFrame in chunks and write each chunk to the file
    for chunk_index, start in enumerate(range(0, total_rows, chunk_size)):
        # Select the slice of the DataFrame for the current chunk
        df_slice = df.iloc[start:start + chunk_size]

        # Determine if headers should be written and the file mode
        write_header = start == 0 and not update
        file_mode = 'w' if write_header else 'a'

        if start == 0 and not update:
            # Overwrite/create file and write headers for the first chunk in non-update mode
            df_slice.to_csv(output_file_path, mode='w', sep="\t", quotechar='"', encoding="UTF-8", index=False)
        elif update:
            # If update mode, check if the file exists
            if not os.path.exists(output_file_path):
                # If file doesn't exist in append mode, write with headers (as if it were a new file)
                df_slice.to_csv(output_file_path, mode='w', sep="\t", quotechar='"', encoding="UTF-8", index=False)
            else:
                # Append the chunk without writing headers
                df_slice.to_csv(output_file_path, mode='a', sep="\t", quotechar='"', encoding="UTF-8", index=False,
                                header=False)

        # Notify progress of written rows (via progress_callback)
        if progress_callback:
            processed_rows = min((chunk_index + 1) * chunk_size, total_rows)
            progress_callback(processed_rows)


def writting_csv(POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, POS_LC_df_insilico, POS_GC_df_insilico, NEG_LC_df_insilico,
                 NEG_GC_df_insilico, output_directory, update=False, progress_callback=None, total_items_callback=None,
                 prefix_callback=None, item_type_callback=None):
    """
    Orchestrates the writing of all structured spectral DataFrames (LC/GC, observed/in-silico, POS/NEG)
    to their respective CSV files using `write_csv`.

    Memory is explicitly managed by deleting each DataFrame after it has been written.

    :param POS_LC_df: DataFrame containing Positive LC data.
    :param POS_GC_df: DataFrame containing Positive GC data.
    :param NEG_LC_df: DataFrame containing Negative LC data.
    :param NEG_GC_df: DataFrame containing Negative GC data.
    :param POS_LC_df_insilico: DataFrame containing Positive LC in-silico data.
    :param POS_GC_df_insilico: DataFrame containing Positive GC in-silico data.
    :param NEG_LC_df_insilico: DataFrame containing Negative LC in-silico data.
    :param NEG_GC_df_insilico: DataFrame containing Negative GC in-silico data.
    :param output_directory: The base directory for output.
    :type output_directory: str
    :param update: Flag indicating whether to append to or overwrite files (default is overwrite).
    :type update: bool
    :return: None
    """

    time.sleep(0.1)
    write_csv(POS_LC_df, "POS_LC.csv", "POS", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del POS_LC_df

    time.sleep(0.1)
    write_csv(POS_GC_df, "POS_GC.csv", "POS", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del POS_GC_df

    time.sleep(0.1)
    write_csv(NEG_LC_df, "NEG_LC.csv", "NEG", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del NEG_LC_df

    time.sleep(0.1)
    write_csv(NEG_GC_df, "NEG_GC.csv", "NEG", update, output_directory, progress_callback=progress_callback,
              total_items_callback=total_items_callback, prefix_callback=prefix_callback,
              item_type_callback=item_type_callback)
    del NEG_GC_df

    time.sleep(0.1)
    write_csv(POS_LC_df_insilico, "POS_LC_In_Silico.csv", "POS", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del POS_LC_df_insilico

    time.sleep(0.1)
    write_csv(POS_GC_df_insilico, "POS_GC_In_Silico.csv", "POS", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del POS_GC_df_insilico

    time.sleep(0.1)
    write_csv(NEG_LC_df_insilico, "NEG_LC_In_Silico.csv", "NEG", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del NEG_LC_df_insilico

    time.sleep(0.1)
    write_csv(NEG_GC_df_insilico, "NEG_GC_In_Silico.csv", "NEG", update, output_directory,
              progress_callback=progress_callback, total_items_callback=total_items_callback,
              prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del NEG_GC_df_insilico


def write_json(update: bool, df: pd.DataFrame, filename: str, mode: str, output_directory: str,
               progress_callback=None, total_items_callback=None,
               prefix_callback=None, item_type_callback=None):
    """
    Writes a DataFrame to a "pretty" JSON file where each record is an element
    in a streaming array. Peak lists are compacted onto a single line to improve readability.

    The function handles writing a new file or appending to an existing JSON array.

    :param update: If True, attempts to append data to an existing file by modifying
                   the trailing ']' character. Otherwise, overwrites or creates the file.
    :type update: bool
    :param df: The DataFrame containing data records to be serialized.
    :type df: pd.DataFrame
    :param filename: The name of the output JSON file.
    :type filename: str
    :param mode: The ionization mode ('POS' or 'NEG'), used for directory path construction.
    :type mode: str
    :param output_directory: The base output directory path.
    :type output_directory: str
    :return: None
    """
    # Construct paths and ensure the directory exists
    output_path = os.path.join(output_directory, "JSON", mode)
    os.makedirs(output_path, exist_ok=True)
    output_file_path = os.path.join(output_path, filename)

    # Set up task description and item type
    if prefix_callback:
        prefix_callback(f"Writing {filename} to JSON:")
    if item_type_callback:
        item_type_callback("rows")

    # Convert DataFrame records to a list of dictionaries
    records = df.to_dict('records')
    total_records = len(records)
    if total_items_callback:
        total_items_callback(total_records, 0)

    # Determine file handling mode for appending vs. writing
    # Append mode is used if 'update' is True AND the file exists and is not empty ('[]' size is 2 bytes).
    is_append_mode = update and os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 2
    open_mode = 'r+' if is_append_mode else 'w'

    try:
        with open(output_file_path, open_mode, encoding='utf-8') as f:
            if is_append_mode:
                # To append, move back 2 characters (overwriting '\n]') to insert a comma and a newline.
                f.seek(0, os.SEEK_END)
                f.seek(f.tell() - 2)
                f.write(',\n')
            else:
                # For a new file, start the JSON array
                f.write('[\n')

            # --- Main loop to write each record ---
            for i, item in enumerate(records):
                # --- Process and cast numerical/structural data for a single record ---
                try:
                    # Cast known numerical fields to float/int, suppressing errors if conversion fails
                    if item.get('MSLEVEL'): item['MSLEVEL'] = int(item['MSLEVEL'])
                    if item.get('PRECURSORMZ'): item['PRECURSORMZ'] = float(item['PRECURSORMZ'])
                    if item.get('RT'): item['RT'] = float(item['RT'])
                    if item.get('ENTROPY'): item['ENTROPY'] = float(item['ENTROPY'])
                except (ValueError, TypeError):
                    pass

                # Handle peak list processing
                num_peaks_str = item.pop('NUM PEAKS', '0')
                peaks_list_str = item.pop('PEAKS_LIST', '')
                try:
                    num_peaks_int = int(num_peaks_str)
                except (ValueError, TypeError):
                    num_peaks_int = 0

                # Parse the ';' separated peak string into a list of lists/tuples
                peaks_array = []
                if isinstance(peaks_list_str, str) and peaks_list_str:
                    for pair in peaks_list_str.strip().split(';'):
                        values = pair.split(maxsplit=2)
                        if len(values) >= 2:
                            try:
                                mz = float(values[0])
                                intensity = float(values[1])
                                if len(values) == 3:
                                    peaks_array.append([mz, intensity, values[2]])
                                else:
                                    peaks_array.append([mz, intensity])
                            except ValueError:
                                continue

                item['NUM PEAKS'] = num_peaks_int
                item['PEAKS_LIST'] = peaks_array

                # --- Generate and format the JSON string ---
                # 1. Dump to standard pretty JSON
                item_str_pretty = json.dumps(item, indent=4, ensure_ascii=False)

                # 2. Compact the peak list array structures onto a single line for better readability
                # Regex for arrays with 3 elements (mz, intensity, annotation)
                item_str_compacted = re.sub(
                    r'\[\n\s*(-?[\d\.eE\+\-]+),\n\s*(-?[\d\.eE\+\-]+),\n\s*"(.*?)"\n\s*\]',
                    r'[\1, \2, "\3"]', item_str_pretty)
                # Regex for arrays with 2 elements (mz, intensity)
                item_str_compacted = re.sub(
                    r'\[\n\s*(-?[\d\.eE\+\-]+),\n\s*(-?[\d\.eE\+\-]+)\n\s*\]',
                    r'[\1, \2]', item_str_compacted)

                # --- Indent the block and write to file ---
                # Indent the entire record string block by 2 spaces
                indented_str = '  ' + item_str_compacted.replace('\n', '\n  ')
                f.write(indented_str)

                # Add a comma unless it's the last record
                if i < total_records - 1:
                    f.write(',\n')
                else:
                    f.write('\n')

                if progress_callback:
                    progress_callback(i + 1)

            # Close the JSON array
            f.write(']')

    except IOError as e:
        # Removed print statement as per user request to remove all prints
        # Handle the error gracefully
        pass


def writting_json(update, POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, POS_LC_df_insilico, POS_GC_df_insilico,
                  NEG_LC_df_insilico, NEG_GC_df_insilico, output_directory, progress_callback=None,
                  total_items_callback=None, prefix_callback=None, item_type_callback=None):
    """
    Orchestrates the writing of all structured spectral DataFrames (LC/GC, observed/in-silico, POS/NEG)
    to their respective JSON files using `write_json`.

    Memory is explicitly managed by deleting each DataFrame after it has been written.

    :param update: Flag indicating whether to append to or overwrite files.
    :type update: bool
    :param POS_LC_df: DataFrame containing Positive LC data.
    :param POS_GC_df: DataFrame containing Positive GC data.
    :param NEG_LC_df: DataFrame containing Negative LC data.
    :param NEG_GC_df: DataFrame containing Negative GC data.
    :param POS_LC_df_insilico: DataFrame containing Positive LC in-silico data.
    :param POS_GC_df_insilico: DataFrame containing Positive GC in-silico data.
    :param NEG_LC_df_insilico: DataFrame containing Negative LC in-silico data.
    :param NEG_GC_df_insilico: DataFrame containing Negative GC in-silico data.
    :param output_directory: The base directory for output.
    :type output_directory: str
    :return: None
    """
    time.sleep(0.1)

    # Write Positive LC
    write_json(update, POS_LC_df, "POS_LC.json", "POS", output_directory, progress_callback=progress_callback,
               total_items_callback=total_items_callback, prefix_callback=prefix_callback,
               item_type_callback=item_type_callback)
    del POS_LC_df

    time.sleep(0.1)
    # Write Positive GC
    write_json(update, POS_GC_df, "POS_GC.json", "POS", output_directory, progress_callback=progress_callback,
               total_items_callback=total_items_callback, prefix_callback=prefix_callback,
               item_type_callback=item_type_callback)
    del POS_GC_df

    time.sleep(0.1)
    # Write Negative LC
    write_json(update, NEG_LC_df, "NEG_LC.json", "NEG", output_directory, progress_callback=progress_callback,
               total_items_callback=total_items_callback, prefix_callback=prefix_callback,
               item_type_callback=item_type_callback)
    del NEG_LC_df

    time.sleep(0.1)
    # Write Negative GC
    write_json(update, NEG_GC_df, "NEG_GC.json", "NEG", output_directory, progress_callback=progress_callback,
               total_items_callback=total_items_callback, prefix_callback=prefix_callback,
               item_type_callback=item_type_callback)
    del NEG_GC_df

    time.sleep(0.1)
    # Write Positive In Silico LC
    write_json(update, POS_LC_df_insilico, "POS_LC_In_Silico.json", "POS", output_directory,
               progress_callback=progress_callback, total_items_callback=total_items_callback,
               prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del POS_LC_df_insilico

    time.sleep(0.1)
    # Write Positive In Silico GC
    write_json(update, POS_GC_df_insilico, "POS_GC_In_Silico.json", "POS", output_directory,
               progress_callback=progress_callback, total_items_callback=total_items_callback,
               prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del POS_GC_df_insilico

    time.sleep(0.1)
    # Write Negative In Silico LC
    write_json(update, NEG_LC_df_insilico, "NEG_LC_In_Silico.json", "NEG", output_directory,
               progress_callback=progress_callback, total_items_callback=total_items_callback,
               prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del NEG_LC_df_insilico

    time.sleep(0.1)
    # Write Negative In Silico GC
    write_json(update, NEG_GC_df_insilico, "NEG_GC_In_Silico.json", "NEG", output_directory,
               progress_callback=progress_callback, total_items_callback=total_items_callback,
               prefix_callback=prefix_callback, item_type_callback=item_type_callback)
    del NEG_GC_df_insilico