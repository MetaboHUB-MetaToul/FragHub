from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import psutil
import json
import sys
import os
import re

# Dynamically retrieve BASE_DIR
if getattr(sys, 'frozen', False):  # If executed from a PyInstaller executable
    BASE_DIR = sys._MEIPASS
else:  # Normal mode (not frozen, executed as a Python script)
    # BASE_DIR points to the parent folder of the project (root)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Build the path to the ontologies_datas folder
ONTOLOGIES_PATH = os.path.join(BASE_DIR, "datas", "ontologies_datas")
PUBCHEM_PATH = os.path.join(BASE_DIR, "datas", "pubchem_datas")
ADDUCT_PATH = os.path.join(BASE_DIR, "datas")
INSTRUMENT_TREE_PATH = os.path.join(BASE_DIR, "datas")
KEYS_PATH = os.path.join(BASE_DIR, "datas")



# =================================================== REGEX PATTERN ====================================================

# ============ Parsors regex ============
global is_adduct_pattern
is_adduct_pattern = re.compile(r"m\]?(\-|\+)", flags=re.IGNORECASE)

global metadata_strip_value_pattern
metadata_strip_value_pattern = re.compile(r"^\"|\"$")

global metadata_fields_name_pattern
metadata_fields_name_pattern = re.compile(r'^[\W_]+|[\W_]+$')

global metadata_pattern_mgf
metadata_pattern_mgf = re.compile(r"([^:\n]*?)=\s*([^\n]*)(?:\n|$)")

global metadata_pattern_msp
metadata_pattern_msp = re.compile(r"([^:]*):(?: )?([^\n]*)(?:\n|$)")

global computed_pattern
computed_pattern = re.compile(r"computed", flags=re.IGNORECASE)

global comment_pattern
comment_pattern = re.compile(r'comment.*', flags=re.IGNORECASE)

global peak_list_split_pattern
peak_list_split_pattern = re.compile(r"(?:^|\n)(-?\d+\.?\d*(?:[Ee][+-]?\d+)?)(?:\s+|:)(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)")

global peak_list_json_pattern
peak_list_json_pattern = re.compile(r"(-?\d+\.?\d*(?:[Ee][+-]?\d+)?)(?:\s+|:|,|, )(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)")

global sub_fields_pattern
sub_fields_pattern = re.compile(r"(\S+?)=\"([^\"]*)\"|\"(\w+?)=([^\"]*)\"|\"([^\"]*?)=([^\"]*)\"|(\S+?)=(\d+(?:[.,]\d*)?)|(\S+?)=(.*?)(?:;|\n|$)")

global metadata_peak_list_split_pattern_mgf
metadata_peak_list_split_pattern_mgf = re.compile(r"([\s\S]*=.*[0-9]*\n)(((-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(\s+|:)(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(.*)(\n|$))*)")

global metadata_peak_list_split_pattern_msp
metadata_peak_list_split_pattern_msp = re.compile(r"([\s\S]*:.*[0-9]*\n)(((-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(\s+|:)(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(.*)(\n|$))*)")
# ======================================

# ===== normalizers regex pattern ======
global indigo_smiles_correction_pattern
indigo_smiles_correction_pattern = re.compile(r"\|[\s\S]*")

global sub_signe_end_adduct_pattern
sub_signe_end_adduct_pattern = re.compile(r"(?<!M)(\-|\+)$")

global sub_adduct_pattern
sub_adduct_pattern = re.compile(r"\(|\)|(.*\[)|(\]([\d\+\-\*]*)?)")

global float_check_pattern
float_check_pattern = re.compile(r"(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)")

global ms_level_pattern
ms_level_pattern = re.compile(r"(?:ms)?(\d)", flags=re.IGNORECASE)

global ionmode_pos_pattern
ionmode_pos_pattern = re.compile(r"^p|^\+|^pos", flags=re.IGNORECASE)

global ionmode_neg_pattern
ionmode_neg_pattern = re.compile(r"^n|^\-|^neg", flags=re.IGNORECASE)

global repair_inchi_pattern
repair_inchi_pattern = re.compile(r"^(inchi=)?", flags=re.IGNORECASE)

global inchi_pattern
inchi_pattern = re.compile(r"InChI=.*|\/[0-9A-Z]*\/", flags=re.IGNORECASE) # Match inchi

global smiles_pattern
smiles_pattern = re.compile(r"[^J][a-z0-9@+\-\[\]\(\)\\\/%=#$]{6,}", flags=re.IGNORECASE) # Match smiles

global inchikey_pattern
inchikey_pattern = re.compile(r"([A-Z]{14}-[A-Z]{10}-[NO])|([A-Z]{14})", flags=re.IGNORECASE) # Match inchikey or short inchikey

global In_Silico_pattern
In_Silico_pattern = re.compile(r"in.silico|insilico|predicted|theoretical|Annotation.level.3", flags=re.IGNORECASE)

global retention_time_pattern
retention_time_pattern = re.compile(r"(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)(?:\W)?(m|min|minute|minutes|s|sec|second|seconds|ms|millisecond|milliseconds)(?:\W)?", flags=re.IGNORECASE)

global ionization_mode_pattern
ionization_mode_pattern = re.compile(r"((?:^|\b)?APCI(?:\b|$)?)|((?:^|\b)?ACPI(?:\b|$)?)|((?:^|\b)?APPI(?:\b|$)?)|((?:^|\b)?EI(?:\b|$)?)|((?:^|\b)?ESI(?:\b|$)?)|((?:^|\b)?FAB(?:\b|$)?)|((?:^|\b)?MALDI(?:\b|$)?)",flags=re.IGNORECASE)

global empty_pattern
empty_pattern = re.compile(r"(^CCS:( .*)?)|(^\$:00in-source( .*)?)|(^0( .*)?)|(^0\.0( .*)?)|(^$)|(^na( .*)?)|(^n/a( .*)?)|(^nan( .*)?)|(^unknown( .*)?)|(^unknow( .*)?)|(^none( .*)?)|(^\?( .*)?)|(^unk( .*)?)|(^x( .*)?)", flags=re.IGNORECASE)
# =====================================

# ======================================================================================================================

# =================================================== READ FILES =======================================================

# 1. On déclare les variables globales à vide pour que l'importation soit instantanée
global ontologies_df, pubchem_datas, adduct_massdiff_dict_POS, adduct_massdiff_dict_NEG
global adduct_dict_POS, adduct_dict_NEG, instrument_tree, keys_dict

ontologies_df = None
pubchem_datas = None
adduct_massdiff_dict_POS = {}
adduct_massdiff_dict_NEG = {}
adduct_dict_POS = {}
adduct_dict_NEG = {}
instrument_tree = {}
keys_dict = {}

# 2. On enferme TOUT le chargement dans cette fonction
def load_internal_databases(step_callback=None):
    global ontologies_df, pubchem_datas, adduct_massdiff_dict_POS, adduct_massdiff_dict_NEG
    global adduct_dict_POS, adduct_dict_NEG, instrument_tree, keys_dict
    
    import time
    start_time = time.time()
    print("🚀 Démarrage du chargement de la base de données via RUST...", flush=True)

    # Sécurité : si c'est déjà chargé, on ne refait pas le travail
    if pubchem_datas is not None:
        return

    if step_callback:
        step_callback("-- LOADING INTERNAL DATABASES (PUBCHEM, ONTOLOGIES...) --")

    try:
        import fraghub_rust
    except ImportError:
        print("❌ Extension Rust introuvable ! Veuillez la compiler avec maturin.", flush=True)
        return

    # --- ONTOLOGIES (RUST) ---
    print("⏳ Chargement des ontologies...", flush=True)
    ontologies_dict_rust = fraghub_rust.load_ontologies_datas(ONTOLOGIES_PATH)
    ontologies_df = pd.DataFrame(ontologies_dict_rust)

    # --- PUBCHEM (RUST) ---
    print("⏳ Chargement de PubChem...", flush=True)
    pubchem_dict_rust = fraghub_rust.load_pubchem_datas(PUBCHEM_PATH)
    pubchem_datas = pd.DataFrame(pubchem_dict_rust)
    # RUST reads everything as string, convert numerical columns back to floats
    if 'EXACTMASS' in pubchem_datas.columns:
        pubchem_datas['EXACTMASS'] = pd.to_numeric(pubchem_datas['EXACTMASS'], errors='coerce')
    if 'AVERAGEMASS' in pubchem_datas.columns:
        pubchem_datas['AVERAGEMASS'] = pd.to_numeric(pubchem_datas['AVERAGEMASS'], errors='coerce')

    # --- ADDUCTS (RUST) ---
    print("⏳ Chargement des Adducts, Instrument Tree et Keys...", flush=True)
    adduct_file_path = os.path.abspath(os.path.join(ADDUCT_PATH, "adduct_to_convert.csv"))
    res_pos, res_massdiff_pos, res_neg, res_massdiff_neg = fraghub_rust.load_adducts(adduct_file_path)
    adduct_dict_POS = res_pos
    adduct_massdiff_dict_POS = res_massdiff_pos
    adduct_dict_NEG = res_neg
    adduct_massdiff_dict_NEG = res_massdiff_neg

    # --- INSTRUMENT TREE (RUST) ---
    instrument_tree_path = os.path.join(INSTRUMENT_TREE_PATH, 'instruments_tree.json')
    instrument_tree = fraghub_rust.load_instrument_tree(instrument_tree_path)

    # --- KEYS (RUST) ---
    keys_file_path = os.path.abspath(os.path.join(KEYS_PATH, "key_to_convert.csv"))
    keys_dict = fraghub_rust.load_keys(keys_file_path)
    
    elapsed = time.time() - start_time
    print(f"✅ Chargement terminé avec succès en {elapsed:.2f} secondes !", flush=True)

# ======================================================================================================================

# =====================================================LIST=============================================================
global keys_list
keys_list = ['FILENAME',
             'FILEHASH',
             'PREDICTED',
             'SPLASH',
             'SPECTRUMID',
             'RESOLUTION',
             'SYNON',
             'IONIZATION',
             'MSLEVEL',
             'FRAGMENTATIONMODE',
             'NAME',
             'PRECURSORMZ',
             'EXACTMASS',
             'AVERAGEMASS',
             'PRECURSORTYPE',
             'INSTRUMENTTYPE',
             'INSTRUMENT',
             'SMILES',
             'INCHI',
             'INCHIKEY',
             'COLLISIONENERGY',
             'FORMULA',
             'RT',
             'IONMODE',
             'COMMENT',
             'ENTROPY',
             'CLASSYFIRE_SUPERCLASS',
             'CLASSYFIRE_CLASS',
             'CLASSYFIRE_SUBCLASS',
             'NPCLASS_PATHWAY',
             'NPCLASS_SUPERCLASS',
             'NPCLASS_CLASS',
             'NUM PEAKS',
             'PEAKS_LIST']

# ======================================================================================================================

# ====================================================OTHER VARS========================================================

global available_memory
available_memory = psutil.virtual_memory().available

global cpu_count
cpu_count = os.cpu_count()  # Number of logical cores

# ======================================================================================================================

atoms_of_life = {
'H': 1.0078250322,   # Hydrogen
'C': 12.000000,      # Carbon
'N': 14.003074004,   # Nitrogen
'O': 15.994914619,   # Oxygen
'F': 18.998403162,   # Fluorine
'Na': 22.98976928,   # Sodium
'Mg': 23.98504170,   # Magnesium
'P':  30.973761998,  # Phosphorus
'S': 31.972071174,   # Sulfur
'Cl': 34.9688527,    # Chlorine
'K': 38.96370649,    # Potassium
'Ca': 39.9625909,    # Calcium
'Mn': 54.938043,     # Manganese
'Fe': 55.934936,     # Iron
'Co': 58.933194,     # Cobalt
'Cu': 62.929597,     # Copper
'Zn': 63.929142,     # Zinc
'Br': 78.918338,     # Bromine
'Se': 79.916522,     # Selenium
'I': 126.90447       # Iodine
}