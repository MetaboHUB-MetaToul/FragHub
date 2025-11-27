import pandas as pd
import scripts.globals_vars
import os


def ontologies_completion(spectrum_list, progress_callback=None, total_items_callback=None,
                          prefix_callback=None, item_type_callback=None):
    """
    Enriches the input DataFrame containing spectral data by merging it with
    predefined ontological information (e.g., ClassyFire, NPClass) based on 'INCHIKEY'.

    The function adds default ontology columns, performs a left merge with
    the global ontologies DataFrame, updates the columns, and cleans up the
    temporary merge columns.

    :param spectrum_list: The DataFrame containing spectral data. Must have an 'INCHIKEY' column.
    :type spectrum_list: pd.DataFrame
    :param progress_callback: Function to update progress during processing. (Optional)
    :type progress_callback: callable or None
    :param total_items_callback: Function to set the total number of items to process. (Optional)
    :type total_items_callback: callable or None
    :param prefix_callback: Function to describe the task being performed. (Optional)
    :type prefix_callback: callable or None
    :param item_type_callback: Function to define the item type being processed. (Optional)
    :type item_type_callback: callable or None
    :return: The enriched DataFrame with completed ontology information.
    :rtype: pd.DataFrame
    """
    # Initialize ontology columns with a default 'NOT FOUND' value
    spectrum_list['CLASSYFIRE_SUPERCLASS'] = "NOT FOUND"
    spectrum_list['CLASSYFIRE_CLASS'] = "NOT FOUND"
    spectrum_list['CLASSYFIRE_SUBCLASS'] = "NOT FOUND"
    spectrum_list['NPCLASS_PATHWAY'] = "NOT FOUND"
    spectrum_list['NPCLASS_SUPERCLASS'] = "NOT FOUND"
    spectrum_list['NPCLASS_CLASS'] = "NOT FOUND"

    # Count the number of unique INCHIKEYs for progress tracking
    num_keys = spectrum_list['INCHIKEY'].nunique()

    # Initialize progress tracking via callbacks
    if prefix_callback:
        prefix_callback("updating ontologies:")

    if item_type_callback:
        item_type_callback("rows")

    if total_items_callback:
        # Set the total items to the number of unique INCHIKEYs
        total_items_callback(num_keys, 0)

    # Perform a left merge of the spectrum list with the global ontologies DataFrame
    # This brings in the ontology data for matching INCHIKEYs from the global data.
    completed_df = pd.merge(
        spectrum_list,
        scripts.globals_vars.ontologies_df[
            ["INCHIKEY", "CLASSYFIRE_SUPERCLASS", "CLASSYFIRE_CLASS", "CLASSYFIRE_SUBCLASS", "NPCLASS_PATHWAY",
             "NPCLASS_SUPERCLASS", "NPCLASS_CLASS"]
        ],
        on='INCHIKEY',
        how='left'
    )

    # Simulate key-by-key update progress (used for external progress bars)
    processed_keys = 0
    for _ in range(num_keys):
        processed_keys += 1
        if progress_callback:
            progress_callback(processed_keys)

    # Update the original columns using the merged columns.
    # The 'y' columns contain the data from the global ontology list (if found).
    # The 'x' columns contain the default 'NOT FOUND' value (or original data).
    # pd.combine_first prioritizes the non-null value from the right ('y') over the left ('x').
    completed_df['CLASSYFIRE_SUPERCLASS'] = completed_df['CLASSYFIRE_SUPERCLASS_y'].combine_first(
        completed_df['CLASSYFIRE_SUPERCLASS_x'])
    completed_df['CLASSYFIRE_CLASS'] = completed_df['CLASSYFIRE_CLASS_y'].combine_first(
        completed_df['CLASSYFIRE_CLASS_x'])
    completed_df['CLASSYFIRE_SUBCLASS'] = completed_df['CLASSYFIRE_SUBCLASS_y'].combine_first(
        completed_df['CLASSYFIRE_SUBCLASS_x'])
    completed_df['NPCLASS_PATHWAY'] = completed_df['NPCLASS_PATHWAY_y'].combine_first(completed_df['NPCLASS_PATHWAY_x'])
    completed_df['NPCLASS_SUPERCLASS'] = completed_df['NPCLASS_SUPERCLASS_y'].combine_first(
        completed_df['NPCLASS_SUPERCLASS_x'])
    completed_df['NPCLASS_CLASS'] = completed_df['NPCLASS_CLASS_y'].combine_first(completed_df['NPCLASS_CLASS_x'])

    # Drop the temporary columns created during the merge (suffixed with '_x' and '_y')
    completed_df.drop(
        columns=[
            'CLASSYFIRE_SUPERCLASS_x', 'CLASSYFIRE_SUPERCLASS_y',
            'CLASSYFIRE_CLASS_x', 'CLASSYFIRE_CLASS_y',
            'CLASSYFIRE_SUBCLASS_x', 'CLASSYFIRE_SUBCLASS_y',
            'NPCLASS_PATHWAY_x', 'NPCLASS_PATHWAY_y',
            'NPCLASS_SUPERCLASS_x', 'NPCLASS_SUPERCLASS_y',
            'NPCLASS_CLASS_x', 'NPCLASS_CLASS_y'
        ],
        inplace=True
    )

    return completed_df