import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import socketio
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from MAIN import MAIN
from scripts.backend_vars import parameters_dict

# 1. Setup global pour stocker la loop
loop = None

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/socket.io", socket_app)

# 2. Capture de la loop au démarrage de FastAPI
@app.on_event("startup")
def startup_event():
    global loop
    loop = asyncio.get_event_loop()

# Modèle (avec correction Pydantic V2)
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
    json_enabled: float = Field(alias='json') # Alias pour éviter conflit avec le mot-clé json
    reset_updates: float

    class Config:
        populate_by_name = True

# 3. Fonction d'émission corrigée
def emit_to_frontend(event, data):
    global loop
    if loop:
        # On utilise la loop capturée au démarrage
        asyncio.run_coroutine_threadsafe(sio.emit(event, data), loop)

# Tes callbacks
def progress_callback(val): emit_to_frontend('progress', val)
def step_callback(val): emit_to_frontend('step', val)
def completion_callback(val): emit_to_frontend('completion', val)
def deletion_callback(val): emit_to_frontend('deletion', val)
# ... ajoute les autres si besoin ...

@app.post("/run-analysis")
async def run_analysis(params: FragHubParams, background_tasks: BackgroundTasks):
    # Utilise model_dump() au lieu de dict() (Fix Pydantic V2)
    params_data = params.model_dump(by_alias=True)

    for key, value in params_data.items():
        parameters_dict[key] = value

    background_tasks.add_task(
        MAIN,
        progress_callback=progress_callback,
        step_callback=step_callback,
        completion_callback=completion_callback,
        deletion_callback=deletion_callback
    )
    return {"status": "started"}

# Dans server_api.py, ajoute ceci :

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)