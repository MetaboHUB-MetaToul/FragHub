# FragHub - Command Line Interface (CLI) Documentation

FragHub now includes a fully featured **Headless CLI mode**. This mode allows you to run the highly optimized Rust parsing and filtering engine directly from your terminal, without launching the Vue.js/Electron graphical user interface.

This is particularly useful for:
- **Server-side automation** (CI/CD, cron jobs, etc.)
- **Batch processing** of massive datasets without GUI overhead
- **Integration** into broader data-science pipelines

---

## 🚀 How to Run

To trigger the CLI mode, you **must** append the `--cli` flag when executing FragHub.

### Running from source (Python)
```bash
python scripts/FragHub.py --cli --input_directory "data/input" --output_directory "data/output"
```

### Running the compiled binary
If FragHub is packaged as an executable (e.g., via PyInstaller/Electron), you can pass the arguments directly to the executable:
```bash
./fraghub.exe --cli --input_directory "data/input" --output_directory "data/output"
```

> [!NOTE]
> When running in CLI mode, FragHub outputs real-time progress bars and cleaning reports directly to your terminal (`stdout`), instead of writing to the debug log file.

---

## 📋 Required Arguments

These arguments must be provided for FragHub to run.

| Argument | Type | Description |
| :--- | :--- | :--- |
| `--input_directory` | `List[str]` | One or multiple paths to input directories or files (MGF, MSP, JSON, CSV). |
| `--output_directory` | `str` | The directory where the cleaned and converted datasets will be saved. |

---

## 🎛️ Filter Arguments (Optional)

FragHub acts as a boolean for filters where `1.0 = True` (Enabled) and `0.0 = False` (Disabled). All filters are **enabled by default** unless specified otherwise, matching the GUI's default behavior.

### General Intensity
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--normalize_intensity` | `1.0` | Normalize the intensity of peaks to 100%. |
| `--remove_peak_above_precursormz` | `1.0` | Remove all peaks with an m/z greater than the precursor m/z. |

### Minimum Peaks Rule
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--check_minimum_peak_requiered` | `1.0` | Enable the minimum peaks threshold filter. |
| `--check_minimum_peak_requiered_n_peaks` | `3.0` | Minimum number of peaks a spectrum must have to be kept. |

### Peak List Reduction
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--reduce_peak_list` | `1.0` | Enable reducing the peak list to the top most intense peaks. |
| `--reduce_peak_list_max_peaks` | `500.0` | The maximum number of top intense peaks to keep per spectrum. |

### Entropy Score Filtering
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--remove_spectrum_under_entropy_score` | `1.0` | Enable spectrum deletion based on its calculated entropy. |
| `--remove_spectrum_under_entropy_score_value` | `0.5` | Threshold below which the spectrum will be deleted. |

### M/Z Range Filtering
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--keep_mz_in_range` | `1.0` | Enable deleting peaks outside a specific m/z range. |
| `--keep_mz_in_range_from_mz` | `50.0` | The minimum m/z allowed. |
| `--keep_mz_in_range_to_mz` | `2000.0` | The maximum m/z allowed. |

### High Peaks Rule
| Argument | Default | Description |
| :--- | :--- | :--- |
| `--check_minimum_of_high_peaks_requiered` | `1.0` | Enable minimum high peaks rule. |
| `--check_minimum_of_high_peaks_requiered_intensity_percent` | `5.0` | What percentage of the base peak defines a "high peak". |
| `--check_minimum_of_high_peaks_requiered_no_peaks` | `2.0` | Minimum number of "high peaks" a spectrum must contain. |

---

## 🔬 De Novo Calculations

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--calculate_de_novo` | `0.0` | Enable De Novo peptide fragment annotation (Requires heavy computation). |
| `--de_novo_ppm_tolerance` | `10.0` | PPM tolerance used during De Novo calculations. |

---

## 💾 Output Formats & Project Management

Specify which formats you want FragHub to generate at the end of the processing pipeline.

| Argument | Default | Description |
| :--- | :--- | :--- |
| `--csv` | `1.0` | Output data as tabular `.csv` files. |
| `--msp` | `1.0` | Output data as `.msp` spectral files. |
| `--json` | `1.0` | Output data as highly compacted `.json` files. |
| `--reset_updates` | `0.0` | If `1.0`, forces FragHub to ignore previously cleaned caches and run everything from scratch in the output directory. |

---

## 💡 Examples

### 1. Simple Execution (Default Settings)
Runs FragHub with all the default filters enabled (mirroring the GUI defaults).
```bash
python scripts/FragHub.py \
  --cli \
  --input_directory "/path/to/my_library.msp" \
  --output_directory "/path/to/output_folder"
```

### 2. Disabling Specific Outputs
Runs FragHub but only outputs JSON files, disabling MSP and CSV generation.
```bash
python scripts/FragHub.py \
  --cli \
  --input_directory "/path/to/my_library.mgf" \
  --output_directory "/path/to/output_folder" \
  --csv 0.0 \
  --msp 0.0 \
  --json 1.0
```

### 3. Strict Custom Filtering
Runs FragHub with very strict entropy and high-peak rules, and enforces a reset of previous project caches.
```bash
python scripts/FragHub.py \
  --cli \
  --input_directory "/data/raw/batch1/" "/data/raw/batch2/" \
  --output_directory "/data/processed/" \
  --reset_updates 1.0 \
  --remove_spectrum_under_entropy_score_value 1.2 \
  --check_minimum_of_high_peaks_requiered_intensity_percent 10.0 \
  --check_minimum_of_high_peaks_requiered_no_peaks 5.0
```
