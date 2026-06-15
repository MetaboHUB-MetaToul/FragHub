from scripts.backend_vars import parameters_dict
from scripts.set_projects import init_project, reset_updates
import scripts.deletion_report as deletion_report
import scripts.globals_vars as g_vars

import fraghub_rust # <-- UNIQUE PONT VERS TOUT LE BACKEND !

# Imports RDKit conservés strictement ici
from rdkit import Chem, RDLogger
from rdkit.Chem.rdMolDescriptors import CalcMolFormula
from rdkit.Chem.Descriptors import ExactMolWt, MolWt
import pandas as pd
import re
import os
import time
import sys
import gc
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class InterruptedError(Exception):
    pass

ordered_columns = ["FILENAME", "FILEHASH", "PREDICTED", "SPLASH", "SPECTRUMID", "RESOLUTION", "SYNON", "IONIZATION", "MSLEVEL", "FRAGMENTATIONMODE", "NAME", "PRECURSORMZ", "EXACTMASS", "AVERAGEMASS", "PRECURSORTYPE", "INSTRUMENTTYPE", "INSTRUMENT", "SMILES", "INCHI", "INCHIKEY", "COLLISIONENERGY", "FORMULA", "RT", "IONMODE", "COMMENT", "ENTROPY", "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS", "NPCLASS_PATHWAY", "NPCLASS_SUPERCLASS", "NPCLASS_CLASS", "NUM PEAKS", "PEAKS_LIST"]

# --- FONCTIONS CACHÉES RDKIT (Anciennement spectrum_normalizer.py et mols_calculation.py) ---
RDLogger.DisableLog('rdApp.*')
FLOAT_PATTERN = re.compile(r"(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)")

def _rdkit_worker(spec):
    pmz_str = str(spec.get("PRECURSORMZ", ""))
    match = FLOAT_PATTERN.search(pmz_str)
    needs_recalc = True
    if match:
        try:
            if float(match.group(1).replace(",", ".")) > 0.0: needs_recalc = False
        except: pass

    if needs_recalc:
        mols = spec.get("INCHI", "")
        if not mols: mols = spec.get("SMILES", "")
        if mols and isinstance(mols, str):
            mol_obj = Chem.MolFromInchi(mols) if 'InChI=' in mols else Chem.MolFromSmiles(mols)
            if mol_obj:
                try: spec["_RDKIT_EXACT_MASS"] = str(ExactMolWt(mol_obj))
                except: pass

def _pre_compute_rdkit_mass_multithreaded(spectrum_list, prefix_callback=None, progress_callback=None, total_items_callback=None, item_type_callback=None):
    total = len(spectrum_list)
    if total_items_callback: total_items_callback(total)
    if prefix_callback: prefix_callback("Preparing RDKit exact masses (Multithreaded)...")
    if item_type_callback: item_type_callback("spectra")
    with ThreadPoolExecutor() as executor:
        for i, _ in enumerate(executor.map(_rdkit_worker, spectrum_list), 1):
            if i % 2000 == 0 and progress_callback: progress_callback(i)
        if progress_callback: progress_callback(total)

def _apply_transformations(inchi_smiles):
    transforms = {}
    if 'InChI=' not in inchi_smiles:
        inchi_smiles = re.sub(g_vars.indigo_smiles_correction_pattern, "", inchi_smiles)
    if isinstance(inchi_smiles, str):
        mol = Chem.MolFromInchi(inchi_smiles) if 'InChI=' in inchi_smiles else Chem.MolFromSmiles(inchi_smiles)
        if mol is not None:
            transforms = {'INCHI': Chem.MolToInchi(mol), 'INCHIKEY': Chem.MolToInchiKey(mol), 'SMILES': Chem.MolToSmiles(mol), 'FORMULA': CalcMolFormula(mol)}
        else:
            transforms = {'INCHI': '', 'INCHIKEY': '', 'SMILES': '', 'FORMULA': ''}

        if transforms:
            mol = Chem.MolFromInchi(transforms['INCHI']) if 'InChI=' in inchi_smiles else Chem.MolFromSmiles(transforms['SMILES'])
            if mol is not None:
                try:
                    transforms['EXACTMASS'] = ExactMolWt(mol)
                    transforms['AVERAGEMASS'] = MolWt(mol)
                except:
                    transforms['EXACTMASS'] = ''
                    transforms['AVERAGEMASS'] = ''
            else:
                transforms['EXACTMASS'] = ''
                transforms['AVERAGEMASS'] = ''
    return transforms

def _mols_derivation_and_calculation(CONCATENATE_DF, output_directory, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    if prefix_callback: prefix_callback("derivation and calculation:")
    if item_type_callback: item_type_callback("rows")

    unique_inchi_smiles = pd.concat([CONCATENATE_DF['INCHI'], CONCATENATE_DF['SMILES']]).dropna().unique()
    if total_items_callback: total_items_callback(len(unique_inchi_smiles), 0)

    unique_transforms = {}
    for i, inchi_smiles in enumerate(unique_inchi_smiles, 1):
        unique_transforms[inchi_smiles] = _apply_transformations(inchi_smiles)
        if progress_callback: progress_callback(i)

    if prefix_callback: prefix_callback("updating rows:")
    if total_items_callback: total_items_callback(len(CONCATENATE_DF), 0)

    results_processed = 0
    def apply_row_mapping(row):
        nonlocal results_processed
        results_processed += 1
        if progress_callback: progress_callback(results_processed)
        original_inchi = row['INCHI'] if pd.notna(row['INCHI']) else None
        original_smiles = row['SMILES'] if pd.notna(row['SMILES']) else None
        if original_inchi and original_inchi in unique_transforms:
            for k, v in unique_transforms[original_inchi].items(): row[k] = v
        elif original_smiles and original_smiles in unique_transforms:
            for k, v in unique_transforms[original_smiles].items(): row[k] = v
        return row

    CONCATENATE_DF = CONCATENATE_DF.apply(apply_row_mapping, axis=1)
    mask = CONCATENATE_DF['INCHIKEY'].str.fullmatch(g_vars.inchikey_pattern, na=False)
    CONCATENATE_DF = CONCATENATE_DF[mask]
    before = len(CONCATENATE_DF)

    critical_columns = ['EXACTMASS', 'AVERAGEMASS', 'SMILES', 'INCHI', 'INCHIKEY']
    rows_to_drop = CONCATENATE_DF[CONCATENATE_DF[critical_columns].isnull().any(axis=1)].copy()
    CONCATENATE_DF = CONCATENATE_DF.dropna(subset=critical_columns)

    if not rows_to_drop.empty:
        rows_to_drop['DELETION_REASON'] = "spectrum deleted because it has neither inchi nor smiles nor inchikey, even after re calculation"
        deletion_dir = os.path.join(output_directory, "DELETED_SPECTRUMS")
        os.makedirs(deletion_dir, exist_ok=True)
        rows_to_drop.to_csv(os.path.join(deletion_dir, "deleted_no_inchi_smiles_inchikey_after_re_calculation.csv"), index=False, sep='\t', encoding='utf-8')

    deletion_report.no_smiles_no_inchi_no_inchikey += (before - len(CONCATENATE_DF))
    return CONCATENATE_DF
# --- FIN FONCTIONS CACHÉES RDKIT ---


def MAIN(progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None, step_callback=None, completion_callback=None, deletion_callback=None, stop_flag=None):
    def check_stop_flag():
        if stop_flag and stop_flag():
            raise InterruptedError("Process stopped by user.")

    output_directory = parameters_dict["output_directory"]

    try:
        if parameters_dict['reset_updates'] == 1.0:
            reset_updates(output_directory)

        init_project(output_directory)

        start_time = time.time()

        input_path = parameters_dict["input_directory"]

        check_stop_flag()

        # STEP 1: convert files to json if needed (Multithreaded)
        # Appel direct à Rust pour le parsing
        FINAL_MSP, FINAL_CSV, FINAL_JSON, FINAL_MGF = fraghub_rust.parsing_to_dict_processing(
            input_path, g_vars.keys_dict, g_vars.keys_list, progress_callback=progress_callback,
            total_items_callback=total_items_callback, prefix_callback=prefix_callback,
            item_type_callback=item_type_callback, step_callback=step_callback
        )
        check_stop_flag()

        files_to_process = False

        if FINAL_MSP or FINAL_CSV or FINAL_JSON or FINAL_MGF:
            files_to_process = True

        if not files_to_process:
            if deletion_callback: deletion_callback("-- THERE IS NO FILES TO PROCESS, EXITING PROCESS --")
            time.sleep(0.01)
            if completion_callback:
                completion_callback(
                    "--- TOTAL TIME: %s ---" % time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
            return 0

        check_stop_flag()

        # STEP 2: generating SPLASH KEY
        time.sleep(0.01)
        if step_callback:
            step_callback("-- GENERATING SPLASH UNIQUE ID --")
        time.sleep(0.01)

        # Appel direct à Rust pour les Splash
        if FINAL_MSP: FINAL_MSP = fraghub_rust.generate_splash_processing(FINAL_MSP, "MSP", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        if FINAL_CSV: FINAL_CSV = fraghub_rust.generate_splash_processing(FINAL_CSV, "CSV", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        if FINAL_JSON: FINAL_JSON = fraghub_rust.generate_splash_processing(FINAL_JSON, "JSON", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)
        if FINAL_MGF: FINAL_MGF = fraghub_rust.generate_splash_processing(FINAL_MGF, "MGF", progress_callback=progress_callback, total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback)

        check_stop_flag()

        # --- DÉBUT DE L'OPTIMISATION MÉMOIRE ET RESPIRATION UI ---
        # 1. On lâche le GIL 100ms pour que Socket.IO envoie le signal "100% terminé" de la tâche précédente à Vue.js
        time.sleep(0.1)

        # 2. On simule un chargement avec un total de 1 pour que Vue.js affiche la barre sans bugger
        if total_items_callback: total_items_callback(1)
        if prefix_callback: prefix_callback("Compiling and transferring data to DataFrame (Please wait)...")
        if progress_callback: progress_callback(0)

        # 3. Nouvelle pause de 100ms pour que ce message parte BIEN avant le blocage de Pandas
        time.sleep(0.1)

        spectrum_list = []

        # Transfert destructif via extend (rapide) + del (libère la RAM)
        if FINAL_MSP:
            spectrum_list.extend(FINAL_MSP)
            del FINAL_MSP

        if FINAL_CSV:
            spectrum_list.extend(FINAL_CSV)
            del FINAL_CSV

        if FINAL_JSON:
            spectrum_list.extend(FINAL_JSON)
            del FINAL_JSON

        if FINAL_MGF:
            spectrum_list.extend(FINAL_MGF)
            del FINAL_MGF

        # On force la libération de la mémoire morte avant l'allocation massive
        gc.collect()

        # Création du DataFrame (C'est ici que Python fige, mais le front est déjà au courant !)
        spectrum_list = pd.DataFrame(spectrum_list, columns=ordered_columns)
        spectrum_list = spectrum_list.astype({col: str for col in ordered_columns if col != 'PEAKS_LIST'})
        # --- FIN DE L'OPTIMISATION ---

        # On valide la petite étape artificielle
        if progress_callback: progress_callback(1)
        time.sleep(0.01)

        # STEP 3: removing duplicatas
        if step_callback:
            step_callback("-- REMOVING DUPLICATAS --")
        time.sleep(0.01)

        # Préparation des données pour Rust (conversion DataFrame -> list de dicts)
        if isinstance(spectrum_list, pd.DataFrame):
            dict_list = spectrum_list.to_dict('records')
        else:
            dict_list = spectrum_list

        # Appel direct à Rust
        dict_list, deleted_count = fraghub_rust.remove_duplicatas_processing(
            dict_list, output_directory, ordered_columns, progress_callback=progress_callback,
            total_items_callback=total_items_callback, prefix_callback=prefix_callback,
            item_type_callback=item_type_callback
        )
        deletion_report.duplicatas_removed = deleted_count
        spectrum_list = dict_list

        if deletion_callback:
            deletion_callback(f"duplicatas removed: {deletion_report.duplicatas_removed}")

        check_stop_flag()

        update = False

        # --- CORRECTION CRITIQUE: RETOUR AU FORMAT LISTE POUR RUST ---
        if isinstance(spectrum_list, pd.DataFrame):
            spectrum_list = spectrum_list.to_dict('records')

        # STEP 4: Checking updates
        time.sleep(0.01)
        if step_callback:
            step_callback("-- CHECKING FOR UPDATES --")
        time.sleep(0.01)

        # Appel direct à Rust
        spectrum_list, update_temp, deleted_count = fraghub_rust.check_for_update_processing(
            spectrum_list, output_directory, ordered_columns, progress_callback=progress_callback,
            total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback
        )
        deletion_report.previously_cleaned = deleted_count
        if deletion_callback:
            deletion_callback(f"previously cleaned: {deletion_report.previously_cleaned}")

        check_stop_flag()

        # CORRECTION: On utilise len() > 0 au lieu de .empty car spectrum_list est une liste standard !
        if spectrum_list is not None and len(spectrum_list) > 0:

            if update_temp:
                update = True

            if parameters_dict['reset_updates'] == 1.0:
                update = False

            # STEP 5: cleaning spectrums (Multithreaded)
            time.sleep(0.01)
            if step_callback:
                step_callback("-- CLEANING SPECTRUMS --")
            time.sleep(0.01)

            _pre_compute_rdkit_mass_multithreaded(spectrum_list, prefix_callback=prefix_callback, progress_callback=progress_callback, total_items_callback=total_items_callback, item_type_callback=item_type_callback)

            # Appel direct à Rust
            spectrum_list = fraghub_rust.spectrum_cleaning_processing(
                spectrum_list, output_directory, ordered_columns, progress_callback=progress_callback,
                total_items_callback=total_items_callback, prefix_callback=prefix_callback, item_type_callback=item_type_callback
            )

            if deletion_callback:
                deletion_callback(
                    f"""
                    No peaks list: {deletion_report.no_peaks_list}
                    No smiles, no inchi, no inchikey: {deletion_report.no_smiles_no_inchi_no_inchikey}
                    No precursor mz: {deletion_report.no_precursor_mz}
                    No or bad adduct: {deletion_report.no_or_bad_adduct}
                    Low entropy score: {deletion_report.low_entropy_score}
                    Minimum peaks not required: {deletion_report.minimum_peaks_not_requiered}
                    All peaks above precursor mz: {deletion_report.all_peaks_above_precursor_mz}
                    No peaks in mz range: {deletion_report.no_peaks_in_mz_range}
                    Minimum high peaks not required: {deletion_report.minimum_high_peaks_not_requiered}
                    """
                )

            check_stop_flag()

            # CORRECTION: Même chose ici, len() == 0 à la place de .empty
            if spectrum_list is None or len(spectrum_list) == 0:
                if deletion_callback: deletion_callback("-- THERE IS NO SPECTRUMS TO PROCESS AFTER CLEANING, EXITING PROCESS --")
                time.sleep(0.01)
                if completion_callback:
                    completion_callback(
                        "--- TOTAL TIME: %s ---" % time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
                return 0

            # --- TRANSITION LISTE -> PANDAS POUR L'ÉTAPE 5 (Mols Calculation) ---
            spectrum_list = pd.DataFrame(spectrum_list, columns=ordered_columns).astype(str)

            # STEP 5 (b): mols derivations and calculations
            time.sleep(0.01)
            if step_callback:
                step_callback("--  MOLS DERIVATION AND MASS CALCULATION --")
            time.sleep(0.01)
            spectrum_list = _mols_derivation_and_calculation(spectrum_list, output_directory,
                                                             progress_callback=progress_callback,
                                                             total_items_callback=total_items_callback,
                                                             prefix_callback=prefix_callback,
                                                             item_type_callback=item_type_callback)

            if deletion_callback:
                deletion_callback(
                    f"No smiles, no inchi, no inchikey (updated): {deletion_report.no_smiles_no_inchi_no_inchikey}")

            check_stop_flag()

            # STEP 6: completing missing metadata from pubchem datas
            time.sleep(0.01)
            if step_callback:
                step_callback("--  COMPLETING FROM PUBCHEM DATAS --")
            time.sleep(0.01)
            spectrum_list = fraghub_rust.complete_from_pubchem_datas(spectrum_list, progress_callback=progress_callback,
                                                                     total_items_callback=total_items_callback,
                                                                     prefix_callback=prefix_callback,
                                                                     item_type_callback=item_type_callback)

            check_stop_flag()

            # STEP 7: completing missing names
            time.sleep(0.01)
            if step_callback:
                step_callback("--  ONTOLOGIES COMPLETION --")
            time.sleep(0.01)
            spectrum_list = fraghub_rust.ontologies_completion_processing(
                spectrum_list,
                progress_callback=progress_callback,
                total_items_callback=total_items_callback,
                prefix_callback=prefix_callback,
                item_type_callback=item_type_callback
            )

            check_stop_flag()

            # STEP 8: DE NOVO CALCULATIONS
            if parameters_dict["calculate_de_novo"] == 1.0:
                time.sleep(0.01)
                if step_callback:
                    step_callback("-- DE NOVO CALCULATIONS --")
                time.sleep(0.01)
                spectrum_list = fraghub_rust.de_novo_calculation_processing(
                    spectrum_list,
                    progress_callback=progress_callback,
                    total_items_callback=total_items_callback,
                    prefix_callback=prefix_callback,
                    item_type_callback=item_type_callback
                )

                check_stop_flag()

            spectrum_list = fraghub_rust.normalize_to_not_found_processing(spectrum_list)

            # STEP 9: SPLITTING
            # -- SPLITTING [POS / NEG] --
            time.sleep(0.01)
            if step_callback:
                step_callback("--  SPLITTING [POS / NEG] --")
            time.sleep(0.01)
            POS_df, NEG_df = fraghub_rust.split_pos_neg(spectrum_list, progress_callback=progress_callback,
                                                        total_items_callback=total_items_callback, prefix_callback=prefix_callback,
                                                        item_type_callback=item_type_callback)
            check_stop_flag()

            # -- SPLITTING [LC / GC] --
            time.sleep(0.01)
            if step_callback:
                step_callback("--  SPLITTING [LC / GC] --")
            time.sleep(0.01)
            POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df = fraghub_rust.split_LC_GC(POS_df, NEG_df,
                                                                                  progress_callback=progress_callback,
                                                                                  total_items_callback=total_items_callback,
                                                                                  prefix_callback=prefix_callback,
                                                                                  item_type_callback=item_type_callback)

            del POS_df
            del NEG_df
            check_stop_flag()

            # -- SPLITTING [EXP / In-Silico] --
            time.sleep(0.01)
            if step_callback:
                step_callback("--  SPLITTING [EXP / In-Silico] --")
            time.sleep(0.01)
            POS_LC_df, POS_LC_In_Silico_df, POS_GC_df, POS_GC_In_Silico_df, NEG_LC_df, NEG_LC_In_Silico_df, NEG_GC_df, NEG_GC_In_Silico_df = fraghub_rust.exp_in_silico_splitter(
                POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, progress_callback=progress_callback,
                total_items_callback=total_items_callback, prefix_callback=prefix_callback,
                item_type_callback=item_type_callback)

            check_stop_flag()

            if parameters_dict["msp"] == 1.0:
                time.sleep(0.01)
                if step_callback:
                    step_callback("--  CONVERTING CSV TO MSP --")
                time.sleep(0.01)
                POS_LC, POS_LC_insilico, POS_GC, POS_GC_insilico, NEG_LC, NEG_LC_insilico, NEG_GC, NEG_GC_insilico = fraghub_rust.csv_to_msp_processing(
                    POS_LC_df, POS_LC_In_Silico_df, POS_GC_df, POS_GC_In_Silico_df, NEG_LC_df, NEG_LC_In_Silico_df,
                    NEG_GC_df, NEG_GC_In_Silico_df, progress_callback=progress_callback,
                    total_items_callback=total_items_callback, prefix_callback=prefix_callback,
                    item_type_callback=item_type_callback)

            check_stop_flag()

            # STEP 10: writting output files
            if parameters_dict["csv"] == 1.0:
                time.sleep(0.01)
                if step_callback:
                    step_callback("--  WRITING CSV --")
                time.sleep(0.01)
                fraghub_rust.writting_csv_processing(
                    POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, POS_LC_In_Silico_df, POS_GC_In_Silico_df,
                    NEG_LC_In_Silico_df, NEG_GC_In_Silico_df, output_directory, update,
                    progress_callback=progress_callback, total_items_callback=total_items_callback,
                    prefix_callback=prefix_callback, item_type_callback=item_type_callback
                )

            check_stop_flag()

            if parameters_dict["msp"] == 1.0:
                time.sleep(0.01)
                if step_callback:
                    step_callback("--  WRITING MSP --")
                time.sleep(0.01)
                fraghub_rust.writting_msp_processing(
                    POS_LC, POS_LC_insilico, POS_GC, POS_GC_insilico, NEG_LC, NEG_LC_insilico, NEG_GC,
                    NEG_GC_insilico, output_directory, update, progress_callback=progress_callback,
                    total_items_callback=total_items_callback, prefix_callback=prefix_callback,
                    item_type_callback=item_type_callback
                )

            check_stop_flag()

            if parameters_dict["json"] == 1.0:
                time.sleep(0.01)
                if step_callback:
                    step_callback("--  WRITING JSON --")
                time.sleep(0.01)
                fraghub_rust.writting_json_processing(
                    update, POS_LC_df, POS_GC_df, NEG_LC_df, NEG_GC_df, POS_LC_In_Silico_df, POS_GC_In_Silico_df,
                    NEG_LC_In_Silico_df, NEG_GC_In_Silico_df, output_directory,
                    progress_callback=progress_callback, total_items_callback=total_items_callback,
                    prefix_callback=prefix_callback, item_type_callback=item_type_callback
                )

            if deletion_callback:
                deletion_callback(
                    f"Total deletions: {sum([deletion_report.duplicatas_removed, deletion_report.previously_cleaned, deletion_report.no_peaks_list, deletion_report.no_smiles_no_inchi_no_inchikey, deletion_report.no_precursor_mz, deletion_report.low_entropy_score, deletion_report.minimum_peaks_not_requiered, deletion_report.all_peaks_above_precursor_mz, deletion_report.no_peaks_in_mz_range, deletion_report.minimum_high_peaks_not_requiered])}"
                )

            # STEP 12: GENERATE REPORT VIA RUST
            current_datetime = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
            fraghub_rust.generate_report_processing(
                output_directory, current_datetime, parameters_dict, deletion_report.__dict__,
                POS_LC_df, POS_LC_In_Silico_df, POS_GC_df, POS_GC_In_Silico_df,
                NEG_LC_df, NEG_LC_In_Silico_df, NEG_GC_df, NEG_GC_In_Silico_df
            )

        else:
            if deletion_callback: deletion_callback("There is no new spectrums to process. Exiting code !")

        check_stop_flag()

        time.sleep(0.01)
        if completion_callback:
            completion_callback(
                "--- TOTAL TIME: %s ---" % time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))

    except InterruptedError:
        if deletion_callback:
            deletion_callback("\n-- PROCESS INTERRUPTED BY USER --")
        # CHOCOBLAST
        # CHOCOBLAST
        # 15 06 2026

    except Exception:
        raise