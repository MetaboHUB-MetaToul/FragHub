import asyncio
import socketio
import uvicorn
import multiprocessing
import traceback
import time
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import sys
import os
import fraghub_rust

parameters_dict = {}

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


is_cli_mode = "--cli" in sys.argv

# Redirection forcée de la sortie standard et d'erreur vers un fichier (SAUF en mode CLI)
if not is_cli_mode:
    log_path = os.path.join(os.path.expanduser("~"), "fraghub_debug.txt")
    sys.stdout = open(log_path, 'w')
    sys.stderr = sys.stdout

print(f"--- Démarrage de FragHub ---")
print(f"CWD: {os.getcwd()}")
print(f"sys.argv: {sys.argv}")

# Variables globales
loop = None
last_emit_time = 0
EMIT_THROTTLE = 0.05  # 20ms pour une fluidité maximale

# Configuration Socket.IO et FastAPI
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@app.on_event("startup")
def startup_event():
    global loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

class FragHubParams(BaseModel):
    input_directory: list
    output_directory: str
    normalize_intensity: float
    remove_peak_above_precursormz: float
    check_minimum_peak_requiered: float
    check_minimum_peak_requiered_n_peaks: float
    reduce_peak_list: float
    reduce_peak_list_max_peaks: float
    remove_spectrum_under_entropy_score: float
    remove_spectrum_under_entropy_score_value: float
    keep_mz_in_range: float
    keep_mz_in_range_from_mz: float
    keep_mz_in_range_to_mz: float
    check_minimum_of_high_peaks_requiered: float
    check_minimum_of_high_peaks_requiered_intensity_percent: float
    check_minimum_of_high_peaks_requiered_no_peaks: float
    calculate_de_novo: float
    de_novo_ppm_tolerance: float
    csv: float
    msp: float
    json_enabled: float = Field(alias='json')
    reset_updates: float

    class Config:
        populate_by_name = True

def emit_to_frontend(event, data):
    global loop, last_emit_time

    # Throttling UNIQUEMENT sur progress — tous les autres événements
    # (total_items, prefix, step, completion, deletion…) passent toujours.
    # Throttler total_items causait des resets perdus → barre qui saute à 100%.
    if event == 'progress':
        current_time = time.time()
        if (current_time - last_emit_time) < EMIT_THROTTLE:
            return
        last_emit_time = current_time

    if loop:
        try:
            asyncio.run_coroutine_threadsafe(sio.emit(event, data), loop)
        except Exception:
            pass

# --- CALLBACKS ---
current_total_items = 0  # <-- Nouvelle variable globale

def progress_callback(*args):
    global last_emit_time, current_total_items
    if args:
        # Si on atteint 100%, on remet le chrono à zéro pour FORCER l'envoi
        if args[0] >= current_total_items:
            last_emit_time = 0

        emit_to_frontend('progress', args[0])

def total_items_callback(*args):
    global last_emit_time, current_total_items
    last_emit_time = 0
    if args:
        current_total_items = args[0]  # <-- On enregistre le maximum
        emit_to_frontend('total_items', args[0])

def prefix_callback(*args):
    global last_emit_time
    last_emit_time = 0
    if args: emit_to_frontend('prefix', args[0])

def item_type_callback(*args):
    if args: emit_to_frontend('item_type', args[0])

def step_callback(*args):
    if args: emit_to_frontend('step', args[0])

def completion_callback(*args):
    if args: emit_to_frontend('completion', args[0])

def deletion_callback(*args):
    if args: emit_to_frontend('deletion', args[0])

# --- GESTION DU STOP ---
global_stop_flag = False
def get_stop_flag(): return global_stop_flag

@app.get("/stop-analysis")
async def stop_analysis():
    global global_stop_flag
    global_stop_flag = True
    return {"status": "stopped"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/init-data")
async def init_data():
    fraghub_rust.load_internal_databases(BASE_DIR)
    return {"status": "loaded"}

# --- EXÉCUTION ---
def execute_main_safely():
    try:
        # Appel direct de la fonction Rust (remplace l'ancien MAIN.py)
        fraghub_rust.main_orchestrator(
            parameters_dict,
            progress_callback,
            total_items_callback,
            prefix_callback,
            item_type_callback,
            step_callback,
            completion_callback,
            deletion_callback,
            get_stop_flag
        )
    except Exception as e:
        # Gestion de l'interruption utilisateur spécifiée dans Rust
        if str(e) == "Process stopped by user.":
            if deletion_callback:
                deletion_callback("\n-- PROCESS INTERRUPTED BY USER --")
        else:
            traceback.print_exc()

@app.post("/run-analysis")
async def run_analysis(params: FragHubParams, background_tasks: BackgroundTasks):
    global global_stop_flag
    global_stop_flag = False
    params_data = params.model_dump(by_alias=True)
    for key, value in params_data.items():
        parameters_dict[key] = value
    background_tasks.add_task(execute_main_safely)
    return {"status": "started"}

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    if is_cli_mode:
        import argparse
        parser = argparse.ArgumentParser(description="FragHub CLI Mode")
        parser.add_argument("--cli", action="store_true", help="Enable CLI mode")
        parser.add_argument("--input_directory", nargs='+', required=True, help="List of input files/directories")
        parser.add_argument("--output_directory", type=str, required=True, help="Output directory path")
        
        # Filtres et options (avec valeurs par défaut identiques à l'UI Vue.js)
        parser.add_argument("--normalize_intensity", type=float, default=1.0)
        parser.add_argument("--remove_peak_above_precursormz", type=float, default=1.0)
        parser.add_argument("--check_minimum_peak_requiered", type=float, default=1.0)
        parser.add_argument("--check_minimum_peak_requiered_n_peaks", type=float, default=3.0)
        parser.add_argument("--reduce_peak_list", type=float, default=1.0)
        parser.add_argument("--reduce_peak_list_max_peaks", type=float, default=500.0)
        parser.add_argument("--remove_spectrum_under_entropy_score", type=float, default=1.0)
        parser.add_argument("--remove_spectrum_under_entropy_score_value", type=float, default=0.5)
        parser.add_argument("--keep_mz_in_range", type=float, default=1.0)
        parser.add_argument("--keep_mz_in_range_from_mz", type=float, default=50.0)
        parser.add_argument("--keep_mz_in_range_to_mz", type=float, default=2000.0)
        parser.add_argument("--check_minimum_of_high_peaks_requiered", type=float, default=1.0)
        parser.add_argument("--check_minimum_of_high_peaks_requiered_intensity_percent", type=float, default=5.0)
        parser.add_argument("--check_minimum_of_high_peaks_requiered_no_peaks", type=float, default=2.0)
        parser.add_argument("--calculate_de_novo", type=float, default=0.0)
        parser.add_argument("--de_novo_ppm_tolerance", type=float, default=10.0)
        parser.add_argument("--csv", type=float, default=1.0)
        parser.add_argument("--msp", type=float, default=1.0)
        parser.add_argument("--json", type=float, default=1.0)
        parser.add_argument("--reset_updates", type=float, default=0.0)
        
        args = parser.parse_args()
        
        # Résolution intelligente des chemins (fichiers et dossiers)
        resolved_files = []
        for path in args.input_directory:
            if os.path.isfile(path):
                resolved_files.append(os.path.abspath(path))
            elif os.path.isdir(path):
                # Parcourt tous les sous-dossiers à la recherche de fichiers valides
                for root, _, files in os.walk(path):
                    for file in files:
                        if file.lower().endswith(('.msp', '.mgf', '.csv', '.json')):
                            resolved_files.append(os.path.abspath(os.path.join(root, file)))
            else:
                print(f"[WARNING] Le chemin spécifié est introuvable : {path}")

        if not resolved_files:
            print("\n[ERROR] Aucun fichier MS valide (.msp, .mgf, .csv, .json) trouvé dans les chemins spécifiés.")
            sys.exit(1)
            
        # Hydratation du parameters_dict avec les fichiers résolus
        args_dict = vars(args)
        args_dict['input_directory'] = resolved_files
        parameters_dict.update(args_dict)
        
        print("\n========================================")
        print("          FragHub CLI Mode Actif          ")
        print("========================================\n")
        
        # Chargement initial des bases
        fraghub_rust.load_internal_databases(BASE_DIR)
        
        # Variables pour la barre de progression en console
        cli_total_items = [0]
        cli_current_prefix = [""]
        
        def cli_progress_callback(val):
            total = cli_total_items[0]
            if total > 0:
                percent = (val / total) * 100
                # Utilisation de \r pour rafraîchir la même ligne
                print(f"\r{cli_current_prefix[0]} {val}/{total} ({percent:.1f}%)", end="", flush=True)
                if val >= total:
                    print() # Nouvelle ligne à 100%
                    
        def cli_total_items_callback(val):
            cli_total_items[0] = val
            
        def cli_prefix_callback(prefix):
            cli_current_prefix[0] = prefix
            print(f"\n>> {prefix}")
            
        def cli_item_type_callback(item_type):
            pass # Non nécessaire en CLI (déjà implicite dans le prefix)
            
        def cli_step_callback(step):
            print(f"\n[STEP] {step}")
            
        def cli_completion_callback(msg):
            print(f"\n[DONE] {msg}\n")
            
        def cli_deletion_callback(msg):
            print(f"[REPORT] {msg}")
            
        def cli_get_stop_flag():
            return False # Pas d'interruption via UI en mode CLI (l'utilisateur fera Ctrl+C)
            
        try:
            # Lancement de l'orchestrateur de façon synchrone dans le thread principal
            fraghub_rust.main_orchestrator(
                parameters_dict,
                cli_progress_callback,
                cli_total_items_callback,
                cli_prefix_callback,
                cli_item_type_callback,
                cli_step_callback,
                cli_completion_callback,
                cli_deletion_callback,
                cli_get_stop_flag
            )
        except Exception as e:
            print(f"\n[ERROR] Une erreur s'est produite : {e}")
            sys.exit(1)
            
        sys.exit(0)
    else:
        # Lancement normal du GUI (FastAPI / Uvicorn / WebSockets)
        uvicorn.run(socket_app, host="127.0.0.1", port=8000)