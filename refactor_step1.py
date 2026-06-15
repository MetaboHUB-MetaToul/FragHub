import os
import re

base_dir = "/Users/adablanc/Documents/PROJETS/FragHub"

# 1. Update FragHub.py
fh_path = os.path.join(base_dir, "scripts", "FragHub.py")
with open(fh_path, "r") as f: content = f.read()
content = content.replace("from scripts.backend_vars import parameters_dict", "parameters_dict = {}")
content = content.replace("def execute_main_safely():\n    try:\n        MAIN(", "def execute_main_safely():\n    try:\n        MAIN(\n            parameters_dict=parameters_dict,")
with open(fh_path, "w") as f: f.write(content)

# 2. Update MAIN.py
main_path = os.path.join(base_dir, "scripts", "MAIN.py")
with open(main_path, "r") as f: content = f.read()
content = content.replace("from scripts.backend_vars import parameters_dict\n", "")
content = content.replace("def MAIN(progress_callback=None", "def MAIN(parameters_dict, progress_callback=None")
content = content.replace("spectrum_cleaning_processing(\n                spectrum_list, output_directory, ordered_columns, deletion_report, progress_callback=progress_callback", "spectrum_cleaning_processing(\n                spectrum_list, output_directory, ordered_columns, deletion_report, parameters_dict, progress_callback=progress_callback")
content = content.replace("de_novo_calculation_processing(\n                    spectrum_list,\n                    progress_callback=progress_callback", "de_novo_calculation_processing(\n                    spectrum_list,\n                    parameters_dict,\n                    progress_callback=progress_callback")
with open(main_path, "w") as f: f.write(content)

# 3. Update Rust splitter.rs
split_path = os.path.join(base_dir, "scripts", "fraghub_rust", "src", "splitter.rs")
with open(split_path, "r") as f: content = f.read()
content = re.sub(r"// Mise à jour de votre fichier global_report en Python ![\s\S]*?\}\n    \}\n\n", "", content)
with open(split_path, "w") as f: f.write(content)

# 4. Update Rust spectrum_cleaning.rs
sc_path = os.path.join(base_dir, "scripts", "fraghub_rust", "src", "spectrum_cleaning.rs")
with open(sc_path, "r") as f: content = f.read()
content = content.replace("ordered_columns: Bound<'py, PyList>,\n    deletion_report: Bound<'py, PyAny>,\n    progress_callback: Option<PyObject>", "ordered_columns: Bound<'py, PyList>,\n    deletion_report: Bound<'py, PyAny>,\n    parameters_dict_py: Bound<'py, PyDict>,\n    progress_callback: Option<PyObject>")
content = re.sub(r"// Importation des paramètres Python \(backend_vars\) sans modifier MAIN\.py !\n\s*let backend_vars = py\.import_bound\(\"scripts\.backend_vars\"\)\?;\n\s*let parameters_dict_py = backend_vars\.getattr\(\"parameters_dict\"\)\?;", "", content)
with open(sc_path, "w") as f: f.write(content)

# 5. Update Rust de_novo_calculation.rs
dn_path = os.path.join(base_dir, "scripts", "fraghub_rust", "src", "de_novo_calculation.rs")
with open(dn_path, "r") as f: content = f.read()
content = content.replace("spectrum_list_df: Bound<'py, PyAny>,\n    progress_callback: Option<PyObject>", "spectrum_list_df: Bound<'py, PyAny>,\n    parameters_dict_py: Bound<'py, PyDict>,\n    progress_callback: Option<PyObject>")
content = re.sub(r"// Récupérer les paramètres\n\s*let backend_vars = py\.import_bound\(\"scripts\.backend_vars\"\)\?;\n\s*let params = backend_vars\.getattr\(\"parameters_dict\"\)\?\.downcast::<PyDict>\(\)\?\.clone\(\);", "let params = parameters_dict_py;", content)
with open(dn_path, "w") as f: f.write(content)

# 6. Delete old python files
os.remove(os.path.join(base_dir, "scripts", "global_report.py"))
os.remove(os.path.join(base_dir, "scripts", "backend_vars.py"))

print("Step 1 OK")
