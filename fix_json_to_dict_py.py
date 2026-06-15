import re

with open("scripts/convertors/json_to_dict.py", "r") as f:
    content = f.read()

# Remplacer ThreadPoolExecutor par une boucle for séquentielle pour éviter la saturation RAM
old_loop = """    while start < end:
        # Use ThreadPoolExecutor to process the chunk
        with concurrent.futures.ThreadPoolExecutor() as executor:
            FINAL_JSON[start:start + chunk_size] = list(
                executor.map(json_to_dict, FINAL_JSON[start:start + chunk_size]))

        # Filter out None results
        FINAL_JSON[start:start + chunk_size] = [
            item for item in FINAL_JSON[start:start + chunk_size] if item is not None
        ]"""

new_loop = """    for i in range(len(FINAL_JSON)):
        FINAL_JSON[i] = json_to_dict(FINAL_JSON[i])
        processed_items += 1
        if processed_items % 1000 == 0 and progress_callback:
            progress_callback(processed_items)
    
    FINAL_JSON = [item for item in FINAL_JSON if item is not None]
    if progress_callback: progress_callback(processed_items)
    return FINAL_JSON
"""

if "concurrent.futures.ThreadPoolExecutor" in content:
    content = re.sub(r"    while start < end:[\s\S]*?\]", new_loop, content)

with open("scripts/convertors/json_to_dict.py", "w") as f:
    f.write(content)

