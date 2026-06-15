import os
with open("scripts/FragHub.py", "r") as f:
    content = f.read()

content = content.replace("from scripts.MAIN import MAIN", "import sys\nimport os\nsys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))\nfrom scripts.MAIN import MAIN")

with open("scripts/FragHub.py", "w") as f:
    f.write(content)
