import fraghub_rust
from rdkit.Chem.Descriptors import ExactMolWt
from rdkit import RDLogger, Chem
import re
from concurrent.futures import ThreadPoolExecutor

# Désactiver les avertissements RDKit
RDLogger.DisableLog('rdApp.*')

# Compilation de la regex en global pour la réutiliser dans tous les threads
FLOAT_PATTERN = re.compile(r"(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)")

def _process_single_spectrum(spec):
    """
    Fonction 'Worker' (Travailleur) qui sera exécutée en parallèle par les threads.
    Elle modifie le dictionnaire 'spec' sur place.
    """
    pmz_str = str(spec.get("PRECURSORMZ", ""))
    match = FLOAT_PATTERN.search(pmz_str)
    needs_recalc = True

    if match:
        try:
            if float(match.group(1).replace(",", ".")) > 0.0:
                needs_recalc = False
        except:
            pass

    if needs_recalc:
        mols = spec.get("INCHI", "")
        if not mols:
            mols = spec.get("SMILES", "")

        if mols and isinstance(mols, str):
            if 'InChI=' in mols:
                mol_obj = Chem.MolFromInchi(mols)
            else:
                mol_obj = Chem.MolFromSmiles(mols)

            if mol_obj:
                try:
                    # ⚠️ INJECTION DE LA MASSE RDKIT PURE DANS UNE CLÉ CACHÉE
                    spec["_RDKIT_EXACT_MASS"] = str(ExactMolWt(mol_obj))
                except:
                    pass

def pre_compute_rdkit_mass_multithreaded(spectrum_list, prefix_callback=None):
    """
    Lance le calcul RDKit en multithreading sur tous les cœurs disponibles.
    """
    if prefix_callback:
        prefix_callback("Preparing RDKit exact masses (Multithreaded)...")

    # ThreadPoolExecutor va automatiquement utiliser le nombre de cœurs logiques de votre CPU
    # La fonction map va distribuer les 600 000 spectres aux différents threads
    with ThreadPoolExecutor() as executor:
        # On utilise un list() pour forcer l'exécution immédiate de l'itérateur
        list(executor.map(_process_single_spectrum, spectrum_list))


def spectrum_cleaning_processing(spectrum_list, output_directory, progress_callback=None, total_items_callback=None, prefix_callback=None, item_type_callback=None):
    if not spectrum_list:
        return spectrum_list

    # 1. PRÉ-TRAITEMENT PYTHON MULTITHREADÉ (Génère _RDKIT_EXACT_MASS à la vitesse de l'éclair)
    pre_compute_rdkit_mass_multithreaded(spectrum_list, prefix_callback)

    ordered_columns = list(spectrum_list[0].keys())

    # 2. NETTOYAGE ET CALCULS RUST (Toujours en Multithread massif)
    final_list = fraghub_rust.spectrum_cleaning_processing(
        spectrum_list,
        output_directory,
        ordered_columns,
        progress_callback=progress_callback,
        total_items_callback=total_items_callback,
        prefix_callback=prefix_callback,
        item_type_callback=item_type_callback
    )

    return final_list