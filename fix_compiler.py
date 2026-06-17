import re

# ===============================================
# 1. SPECTRUM CLEANING
# ===============================================
with open('scripts/fraghub_rust/src/spectrum_cleaning.rs', 'r') as f:
    content = f.read()

content = re.sub(
    r"pub fn spectrum_cleaning_processing\([\s\S]*?\) -> PyResult<Vec<Spectrum>> \{",
    """pub fn spectrum_cleaning_processing(
    py: Python,
    spectrum_list: Vec<Spectrum>,
    output_directory: String,
    ordered_columns: Vec<String>,
    deletion_report: &mut crate::deletion_report::DeletionReport,
    parameters_dict: &std::collections::HashMap<String, f64>,
    progress_callback: Option<PyObject>,
    total_items_callback: Option<PyObject>,
    prefix_callback: Option<PyObject>,
    item_type_callback: Option<PyObject>,
) -> PyResult<Vec<Spectrum>> {""",
    content
)

old_params = """    let mut parameters_dict: HashMap<String, f64> = HashMap::new();
    if let Ok(dict) = parameters_dict_py.downcast::<PyDict>() {
        for (k, v) in dict.iter() {
            if let Ok(key_str) = k.extract::<String>() {
                if let Ok(val_float) = v.extract::<f64>() {
                    parameters_dict.insert(key_str, val_float);
                }
            }
        }
    }"""
content = content.replace(old_params, "")

with open('scripts/fraghub_rust/src/spectrum_cleaning.rs', 'w') as f:
    f.write(content)


# ===============================================
# 2. MAIN ORCHESTRATOR
# ===============================================
with open('scripts/fraghub_rust/src/main_orchestrator.rs', 'r') as f:
    content = f.read()

old_clean = """        spectrum_list = spectrum_cleaning_processing(
            py, spectrum_list.clone(), output_directory.clone(), ordered_columns.clone(), deletion_report_bound.clone().into_any(), parameters_dict.clone(),
            progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone()
        )?;"""
new_clean = """        spectrum_list = spectrum_cleaning_processing(
            py, spectrum_list, output_directory.clone(), ordered_columns.clone(), &mut deletion_report, &params_f64,
            progress_callback.clone(), total_items_callback.clone(), prefix_callback.clone(), item_type_callback.clone()
        )?;"""
content = content.replace(old_clean, new_clean)

# Also fix generate_report_processing
old_report = """        let deletion_dict = deletion_report_bound.call_method0("to_dict")?.downcast_into::<PyDict>()?;

        generate_report_processing(py, output_directory, current_datetime, &parameters_dict.clone(), &deletion_dict.clone(), &pos_lc_df, &pos_lc_in_silico_df, &pos_gc_df, &pos_gc_in_silico_df, &neg_lc_df, &neg_lc_in_silico_df, &neg_gc_df, &neg_gc_in_silico_df)?;"""

new_report = """        generate_report_processing(py, output_directory, current_datetime, &params_f64, &input_paths, &deletion_report, &pos_lc_df, &pos_lc_in_silico_df, &pos_gc_df, &pos_gc_in_silico_df, &neg_lc_df, &neg_lc_in_silico_df, &neg_gc_df, &neg_gc_in_silico_df)?;"""
content = content.replace(old_report, new_report)

# fallback for another version of the report call
old_report_2 = """        let deletion_dict = deletion_report_bound.call_method0("to_dict")?.downcast_into::<PyDict>()?;
        
        generate_report_processing(py, output_directory, current_datetime, &parameters_dict.clone(), deletion_dict.clone(), &pos_lc_df, &pos_lc_in_silico_df, &pos_gc_df, &pos_gc_in_silico_df, &neg_lc_df, &neg_lc_in_silico_df, &neg_gc_df, &neg_gc_in_silico_df)?;"""
content = content.replace(old_report_2, new_report)

old_report_3 = """        let deletion_dict = deletion_report_bound.call_method0("to_dict")?.downcast_into::<PyDict>()?;
        
        generate_report_processing(py, output_directory, current_datetime, parameters_dict.clone(), deletion_dict.clone(), &pos_lc_df, &pos_lc_in_silico_df, &pos_gc_df, &pos_gc_in_silico_df, &neg_lc_df, &neg_lc_in_silico_df, &neg_gc_df, &neg_gc_in_silico_df)?;"""
content = content.replace(old_report_3, new_report)

with open('scripts/fraghub_rust/src/main_orchestrator.rs', 'w') as f:
    f.write(content)


# ===============================================
# 3. DELETION REPORT
# ===============================================
with open('scripts/fraghub_rust/src/deletion_report.rs', 'w') as f:
    f.write('''// src/deletion_report.rs

#[derive(Clone, Default, Debug)]
pub struct DeletionReport {
    pub duplicatas_removed: usize,
    pub previously_cleaned: usize,
    pub no_peaks_list: usize,
    pub no_smiles_no_inchi_no_inchikey: usize,
    pub no_precursor_mz: usize,
    pub low_entropy_score: usize,
    pub minimum_peaks_not_requiered: usize,
    pub all_peaks_above_precursor_mz: usize,
    pub no_peaks_in_mz_range: usize,
    pub minimum_high_peaks_not_requiered: usize,
    pub no_or_bad_adduct: usize,
}
''')

