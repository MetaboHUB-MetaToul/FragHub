import re

with open("scripts/MAIN.py", "r") as f:
    content = f.read()

content = content.replace("import scripts.globals_vars as g_vars", """
import re
indigo_smiles_correction_pattern = re.compile(r"\|[\s\S]*")
inchikey_pattern = re.compile(r"([A-Z]{14}-[A-Z]{10}-[NO])|([A-Z]{14})", flags=re.IGNORECASE)
""")

content = content.replace("g_vars.indigo_smiles_correction_pattern", "indigo_smiles_correction_pattern")
content = content.replace("g_vars.inchikey_pattern", "inchikey_pattern")
content = content.replace("input_path, g_vars.keys_dict, g_vars.keys_list, progress_callback=progress_callback", "input_path, progress_callback=progress_callback")

with open("scripts/MAIN.py", "w") as f:
    f.write(content)
print("Updated MAIN.py")
