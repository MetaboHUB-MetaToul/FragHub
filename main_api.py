from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# --- 1. DÉFINITION DES PARAMÈTRES (Remplace global_vars.parameters_dict) ---
class FragHubParameters(BaseModel):
    input_directory: List[str]
    output_directory: str

    # De Novo Settings
    calculate_de_novo: bool = False
    de_novo_ppm_tolerance: float = 10.0

    # Filters Settings (Exemples)
    normalize_intensity: bool = True
    remove_peak_above_precursormz: bool = True
    check_minimum_peak_requiered: bool = True
    check_minimum_peak_requiered_n_peaks: float = 3.0
    # Ajoute ici tous les autres paramètres de tes filtres...

    # Output Settings
    output_csv: bool = True
    output_msp: bool = True
    output_json: bool = True

    # Projects Settings
    reset_updates: bool = False

# --- 2. INITIALISATION DE L'API ---
app = FastAPI(title="FragHub API", version="2.0.0")

# Configuration CORS indispensable pour que Nuxt (port 3000) puisse parler à FastAPI (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Autorise le serveur de dev Nuxt
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. ROUTES DE L'API ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API FragHub"}

@app.post("/api/start")
def start_processing(params: FragHubParameters):
    """
    Cette route remplace ta fonction open_progress_window() / start_execution().
    Elle reçoit la configuration de Nuxt et lance le traitement.
    """
    # Vérification basique (bien que Pydantic gère déjà les types)
    if not params.input_directory:
        raise HTTPException(status_code=400, detail="Au moins un fichier d'entrée est requis.")
    if not params.output_directory:
        raise HTTPException(status_code=400, detail="Un dossier de sortie est requis.")

    # Ici, nous appellerons ta fonction 'run_main_in_worker' ou équivalent.
    # Pour l'instant, on simule une réponse de succès :
    print(f"Démarrage de FragHub avec {len(params.input_directory)} fichier(s) vers {params.output_directory}")
    print(f"Calcul de novo activé : {params.calculate_de_novo}")

    return {
        "status": "success",
        "message": "Traitement démarré",
        "received_parameters": params
    }