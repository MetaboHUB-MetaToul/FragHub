import fraghub_rust
import pandas as pd
import os
import time
import gc
from datetime import datetime

class InterruptedError(Exception):
    pass

ordered_columns = ["FILENAME", "FILEHASH", "PREDICTED", "SPLASH", "SPECTRUMID", "RESOLUTION", "SYNON", "IONIZATION", "MSLEVEL", "FRAGMENTATIONMODE", "NAME", "PRECURSORMZ", "EXACTMASS", "AVERAGEMASS", "PRECURSORTYPE", "INSTRUMENTTYPE", "INSTRUMENT", "SMILES", "INCHI", "INCHIKEY", "COLLISIONENERGY", "FORMULA", "RT", "IONMODE", "COMMENT", "ENTROPY", "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS", "NPCLASS_PATHWAY", "NPCLASS_SUPERCLASS", "NPCLASS_CLASS", "NUM PEAKS", "PEAKS_LIST"]

def MAIN(parameters_dict, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None, step_callback=None, completion_callback=None, deletion_callback=None, stop_flag=None):
    def check_stop_flag():
        if stop_flag and stop_flag():
            raise InterruptedError("Process stopped by user.")

    output_directory = parameters_dict["output_directory"]

    try:
        deletion_report = fraghub_rust.DeletionReport()

        if parameters_dict['reset_updates'] == 1.0:
            fraghub_rust.reset_updates(output_directory)
        fraghub_rust.init_project(output_directory)

        start_time = time.time()
        input_path = parameters_dict["input_directory"]
        check_stop_flag()

        # STEP 1: PARSING
        FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF = fraghub_rust.parsing_to_dict_processing(
            input_path, progress_callback=progress_callback, total_items_callback=total_items_callback,
            prefix_callback=prefix_callback, item_type_callback=item_type_callback, step_callback=step_callback
        )
        check_stop_flag()

        if not (FINAL_MSP or FINAL_CSV or FINAL_JSON or FINAL_MGF):
            if deletion_callback: deletion_callback("-- THERE IS NO FILES TO PROCESS --")
            if completion_callback: completion_callback("--- TOTAL TIME: %s ---" % time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
            return 0

        # STEP 2: SPLASH KEY
        time.sleep(0.01)
        if step_callback: step_callback("-- GENERATING SPLASH UNIQUE ID --")
        time.sleep(0.01)

        if FINAL_MSP: FINAL_MSP = fraghub_rust.generate_splash_processing(FINAL_MSP, "MSP", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        if FINAL_CSV: FINAL_CSV = fraghub_rust.generate_splash_processing(FINAL_CSV, "CSV", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        if FINAL_JSON: FINAL_JSON = fraghub_rust.generate_splash_processing(FINAL_JSON, "JSON", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        if FINAL_MGF: FINAL_MGF = fraghub_rust.generate_splash_processing(FINAL_MGF, "MGF", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        check_stop_flag()

        time.sleep(0.1)
        if total_items_callback: total_items_callback(1)
        if prefix_callback: prefix_callback("Merging files (Please wait)...")
        if progress_callback: progress_callback(0)
        time.sleep(0.1)

        spectrum_list = []
        if FINAL_MSP: spectrum_list.extend(FINAL_MSP); del FINAL_MSP
        if FINAL_CSV: spectrum_list.extend(FINAL_CSV); del FINAL_CSV
        if FINAL_JSON: spectrum_list.extend(FINAL_JSON); del FINAL_JSON
        if FINAL_MGF: spectrum_list.extend(FINAL_MGF); del FINAL_MGF
        gc.collect()
        
        if progress_callback: progress_callback(1)
        time.sleep(0.01)

        # STEP 3: DUPLICATAS
        if step_callback: step_callback("-- REMOVING DUPLICATAS --")
        time.sleep(0.01)

        spectrum_list, deleted_count = fraghub_rust.remove_duplicatas_processing(
            spectrum_list, output_directory, ordered_columns, progress_callback=progress_callback,
            total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback
        )
        deletion_report.duplicatas_removed = deleted_count
        if deletion_callback: deletion_callback(f"duplicatas removed: {deletion_report.duplicatas_removed}")
        check_stop_flag()

        # STEP 4: UPDATES
        update = False
        time.sleep(0.01)
        if step_callback: step_callback("-- CHECKING FOR UPDATES --")
        time.sleep(0.01)

        spectrum_list, update_temp, deleted_count = fraghub_rust.check_for_update_processing(
            spectrum_list, output_directory, ordered_columns, progress_callback=progress_callback,
            total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback
        )
        deletion_report.previously_cleaned = deleted_count
        if deletion_callback: deletion_callback(f"previously cleaned: {deletion_report.previously_cleaned}")
        check_stop_flag()

        if spectrum_list and len(spectrum_list) > 0:
            if update_temp: update = True
            if parameters_dict['reset_updates'] == 1.0: update = False

            # STEP 5: CLEANING
            time.sleep(0.01)
            if step_callback: step_callback("-- CLEANING SPECTRUMS --")
            time.sleep(0.01)

            spectrum_list = fraghub_rust.spectrum_cleaning_processing(
                spectrum_list, output_directory, ordered_columns, deletion_report, parameters_dict,
                progress_callback=progress_callback, total_items_callback=total_items_callback,
                prefix_callback=prefix_callback, item_type_callback=item_type_callback
            )

            if not spectrum_list or len(spectrum_list) == 0:
                if deletion_callback: deletion_callback("-- THERE IS NO SPECTRUMS TO PROCESS AFTER CLEANING --")
                if completion_callback: completion_callback("--- TOTAL TIME: %s ---" % time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
                return 0
            check_stop_flag()

            # STEP 6: MOLS DERIVATIONS (RDKit in Rust)
            time.sleep(0.01)
            if step_callback: step_callback("--  MOLS DERIVATION AND MASS CALCULATION --")
            time.sleep(0.01)
            spectrum_list = fraghub_rust.process_mols(
                spectrum_list, output_directory, deletion_report,
                progress_callback=progress_callback, total_items_callback=total_items_callback,
                prefix_callback=prefix_callback, item_type_callback=item_type_callback
            )
            check_stop_flag()

            # CONVERSION EN PANDAS POUR LA SUITE
            spectrum_list = pd.DataFrame(spectrum_list, columns=ordered_columns).astype(str)

            # STEP 7: PUBCHEM
            time.sleep(0.01)
            if step_callback: step_callback("--  COMPLETING FROM PUBCHEM DATAS --")
            time.sleep(0.01)
            spectrum_list = fraghub_rust.complete_from_pubchem_datas(
                spectrum_list, progress_callback=progress_callback, total_items_callback=total_items_callback,
                prefix_callback=prefix_callback, item_type_callback=item_type_callback
            )
            check_stop_flag()

            # STEP 8: ONTOLOGIES
            time.sleep(0.01)
            if step_callback: step_callback("--  ONTOLOGIES COMPLETION --")
            time.sleep(0.01)
            spectrum_list = fraghub_rust.ontologies_completion_processing(
                spectrum_list, progress_callback=progress_callback, total_items_callback=total_items_callback,
                prefix_callback=prefix_callback, item_type_callback=item_type_callback
            )
            check_stop_flag()

            # STEP 9: DE NOVO
            if parameters_dict.get("calculate_de_novo", 0.0) == 1.0:
                time.sleep(0.01)
                if step_callback: step_callback("-- DE NOVO CALCULATIONS --")
                time.sleep(0.01)
                spectrum_list = fraghub_rust.de_novo_calculation_processing(
                    spectrum_list, parameters_dict, progress_callback=progress_callback,
                    total_items_callback=total_items_callback, prefix_callback=prefix_callback,
                    item_type_callback=item_type_callback
                )
                check_stop_flag()

            spectrum_list = fraghub_rust.normalize_to_not_found_processing(spectrum_list)

            # STEP 10: SPLITTING
            time.sleep(0.01)
            if step_callback: step_callback("--  SPLITTING [POS / NEG] --")
            time.sleep(0.01)
            POS_df, NEG_df = fraghub_rust.split_pos_neg(spectrum_list, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            
            time.sleep(0.01)
            if step_callback: step_callback("--  SPLITTING [LC / GC] --")
            time.sleep(0.01)
            POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df = fraghub_rust.split_LC_GC(POS_df, NEG_df, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            del POS_df; del NEG_df
            
            time.sleep(0.01)
            if step_callback: step_callback("--  SPLITTING [EXP / In-Silico] --")
            time.sleep(0.01)
            POS_LC_df, POS_LC_In_Silico_df, POS_GC_df, POS_GC_In_Silico_df, NEG_LC_df, NEG_LC_In_Silico_df, NEG_GC_df, NEG_GC_In_Silico_df = fraghub_rust.exp_in_silico_splitter(POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            check_stop_flag()

            # STEP 11: MSP / CSV / JSON
            if parameters_dict.get("msp", 0.0) == 1.0:
                time.sleep(0.01)
                if step_callback: step_callback("--  CONVERTING CSV TO MSP --")
                time.sleep(0.01)
                POS_LC, POS_LC_insilico, POS_GC, POS_GC_insilico, NEG_LC, NEG_LC_insilico, NEG_GC, NEG_GC_insilico = fraghub_rust.csv_to_msp_processing(POS_LC_df, POS_LC_In_Silico_df, POS_GC_df, POS_GC_In_Silico_df, NEG_LC_df, NEG_LC_In_Silico_df, NEG_GC_df, NEG_GC_In_Silico_df, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            check_stop_flag()

            if parameters_dict.get("csv", 0.0) == 1.0:
                time.sleep(0.01)
                if step_callback: step_callback("--  WRITING CSV --")
                time.sleep(0.01)
                fraghub_rust.writting_csv_processing(POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, POS_LC_In_Silico_df, POS_GC_In_Silico_df, NEG_LC_In_Silico_df, NEG_GC_In_Silico_df, output_directory, update, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
            
            if parameters_dict.get("msp", 0.0) == 1.0:
                time.sleep(0.01)
                if step_callback: step_callback("--  WRITING MSP --")
                time.sleep(0.01)
                fraghub_rust.writting_msp_processing(POS_LC, POS_LC_insilico, POS_GC, POS_GC_insilico, NEG_LC, NEG_LC_insilico, NEG_GC, NEG_GC_insilico, output_directory, update, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

            if parameters_dict.get("json", 0.0) == 1.0:
                time.sleep(0.01)
                if step_callback: step_callback("--  WRITING JSON --")
                time.sleep(0.01)
                fraghub_rust.writting_json_processing(update, POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, POS_LC_In_Silico_df, POS_GC_In_Silico_df, NEG_LC_In_Silico_df, NEG_GC_In_Silico_df, output_directory, progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

            if deletion_callback:
                deletion_callback(f"Total deletions: {sum([deletion_report.duplicatas_removed, deletion_report.previously_cleaned, deletion_report.no_peaks_list, deletion_report.no_smiles_no_inchi_no_inchikey, deletion_report.no_precursor_mz, deletion_report.low_entropy_score, deletion_report.minimum_peaks_not_requiered, deletion_report.all_peaks_above_precursor_mz, deletion_report.no_peaks_in_mz_range, deletion_report.minimum_high_peaks_not_requiered])}")

            # STEP 12: REPORT
            current_datetime = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
            fraghub_rust.generate_report_processing(output_directory, current_datetime, parameters_dict, deletion_report.to_dict(), POS_LC_df, POS_LC_In_Silico_df, POS_GC_df, POS_GC_In_Silico_df, NEG_LC_df, NEG_LC_In_Silico_df, NEG_GC_df, NEG_GC_In_Silico_df)

        if completion_callback: completion_callback("--- TOTAL TIME: %s ---" % time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

    except InterruptedError:
        if deletion_callback: deletion_callback("\n-- PROCESS INTERRUPTED BY USER --")
