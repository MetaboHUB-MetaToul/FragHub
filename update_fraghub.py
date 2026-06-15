import os

with open("scripts/FragHub.py", "r") as f:
    content = f.read()

content = content.replace("import scripts.globals_vars as g_vars", "import fraghub_rust")

code_to_insert = """
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
"""

content = content.replace("import sys\nimport os", f"import sys\nimport os\n{code_to_insert}")
content = content.replace("g_vars.load_internal_databases()", "fraghub_rust.load_internal_databases(BASE_DIR)")

with open("scripts/FragHub.py", "w") as f:
    f.write(content)

print("Updated FragHub.py")
