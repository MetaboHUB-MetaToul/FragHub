import asyncio
import socketio
import uvicorn
import multiprocessing
import traceback
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scripts.MAIN import MAIN
from scripts.backend_vars import parameters_dict
import scripts.globals_vars as g_vars

loop = None

# --- 1. CORRECTION DU ROUTAGE SOCKET.IO ---
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# On enveloppe FastAPI DANS SocketIO
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@app.on_event("startup")
def startup_event():
    global loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
    print("[OK] Serveur FastAPI et Socket.IO prets !")

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
    global loop
    # --- 2. LE MOUCHARD : SANS EMOJIS POUR WINDOWS ---
    print(f"[EMIT VERS VUE.JS] {event.upper()} : {data}")

    if loop:
        try:
            asyncio.run_coroutine_threadsafe(sio.emit(event, data), loop)
        except Exception as e:
            print(f"[WARNING] Erreur de communication Socket: {e}")

# --- CALLBACKS BOUCLIERS ---
def progress_callback(*args):
    if args: emit_to_frontend('progress', args[0])
def total_items_callback(*args):
    if args: emit_to_frontend('total_items', args[0])
def prefix_callback(*args):
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

@app.get("/init-data")
async def init_data():
    g_vars.load_internal_databases()
    return {"status": "loaded"}

# --- 3. LE BOUCLIER ANTI-CRASH SILENCIEUX ---
def execute_main_safely():
    print("\n[START] Lancement de MAIN.py en tache de fond...")
    try:
        MAIN(
            progress_callback=progress_callback,
            total_items_callback=total_items_callback,
            prefix_callback=prefix_callback,
            item_type_callback=item_type_callback,
            step_callback=step_callback,
            completion_callback=completion_callback,
            deletion_callback=deletion_callback,
            stop_flag=get_stop_flag
        )
    except Exception as e:
        print(f"\n[ERROR] ERREUR CRITIQUE DANS MAIN.PY :")
        traceback.print_exc() # Imprime l'erreur exacte dans ta console !
        emit_to_frontend('deletion', f"CRASH: {str(e)}")
        emit_to_frontend('completion', "PROCESS FAILED (Check console)")

@app.post("/run-analysis")
async def run_analysis(params: FragHubParams, background_tasks: BackgroundTasks):
    global global_stop_flag
    global_stop_flag = False

    params_data = params.model_dump(by_alias=True)
    for key, value in params_data.items():
        parameters_dict[key] = value

    background_tasks.add_task(execute_main_safely)
    return {"status": "started"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    multiprocessing.freeze_support()
    uvicorn.run(socket_app, host="127.0.0.1", port=8000)