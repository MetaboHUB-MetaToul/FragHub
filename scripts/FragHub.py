import asyncio
import socketio
import uvicorn
import multiprocessing
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scripts.MAIN import MAIN
# ON IMPORTE DEPUIS LE NOUVEAU FICHIER (plus aucun lien avec PyQt)
from scripts.backend_vars import parameters_dict
import scripts.globals_vars as g_vars


loop = None

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/socket.io", socket_app)

@app.on_event("startup")
def startup_event():
    global loop
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
    global loop
    if loop:
        asyncio.run_coroutine_threadsafe(sio.emit(event, data), loop)

# --- TOUS TES CALLBACKS SONT LÀ (Même ceux pour la progress bar !) ---
def progress_callback(val): emit_to_frontend('progress', val)
def total_items_callback(val): emit_to_frontend('total_items', val)
def prefix_callback(val): emit_to_frontend('prefix', val)
def item_type_callback(val): emit_to_frontend('item_type', val)
def step_callback(val): emit_to_frontend('step', val)
def completion_callback(val): emit_to_frontend('completion', val)
def deletion_callback(val): emit_to_frontend('deletion', val)


@app.get("/init-data")
async def init_data():
    # Déclenche le chargement multithreadé de PubChem et des ontologies
    g_vars.load_internal_databases()
    return {"status": "loaded"}

@app.post("/run-analysis")
async def run_analysis(params: FragHubParams, background_tasks: BackgroundTasks):
    params_data = params.model_dump(by_alias=True)

    # Ta logique est conservée : on met à jour le dict global en mémoire
    for key, value in params_data.items():
        parameters_dict[key] = value

    # On passe tous les callbacks requis par MAIN
    background_tasks.add_task(
        MAIN,
        progress_callback=progress_callback,
        total_items_callback=total_items_callback,
        prefix_callback=prefix_callback,
        item_type_callback=item_type_callback,
        step_callback=step_callback,
        completion_callback=completion_callback,
        deletion_callback=deletion_callback
    )
    return {"status": "started"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    # Sécurité vitale pour empêcher le Silent Crash sous Windows compilé
    multiprocessing.freeze_support()
    uvicorn.run(app, host="127.0.0.1", port=8000)