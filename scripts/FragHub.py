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


# Redirection forcée de la sortie standard et d'erreur vers un fichier
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
    uvicorn.run(socket_app, host="127.0.0.1", port=8000)