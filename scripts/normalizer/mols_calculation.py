from rdkit.Chem.rdMolDescriptors import CalcMolFormula
from rdkit.Chem.Descriptors import ExactMolWt, MolWt
from rdkit import RDLogger, Chem
import scripts.deletion_report
import scripts.globals_vars
import pandas as pd
import re
import os

# Disable RDKit log (warning) messages for cleaner output.
RDLogger.DisableLog('rdApp.*')


def apply_transformations(inchi_smiles):
    """
    Apply chemical transformations (InChI, InChIKey, SMILES, Formula, Masses)
    to a given InChI or SMILES string using RDKit.

    :param inchi_smiles: The input chemical string (InChI or SMILES).
    :type inchi_smiles: str
    :return: A dictionary containing the transformed chemical properties.
    :rtype: dict
    """
    transforms = {}

    # Correct the input string if it's not in InChI format by removing unwanted patterns.
    if 'InChI=' not in inchi_smiles:
        inchi_smiles = re.sub(scripts.globals_vars.indigo_smiles_correction_pattern,
                               "",
                               inchi_smiles)

    if isinstance(inchi_smiles, str):
        # Determine the input format and attempt to create an RDKit molecule object.
        if 'InChI=' in inchi_smiles:
            mol = Chem.MolFromInchi(inchi_smiles)
        else:
            mol = Chem.MolFromSmiles(inchi_smiles)

        # If a valid molecule object is created, calculate basic chemical identifiers.
        if mol is not None:
            transforms = {
                'INCHI': Chem.MolToInchi(mol),
                'INCHIKEY': Chem.MolToInchiKey(mol),
                'SMILES': Chem.MolToSmiles(mol),
                'FORMULA': CalcMolFormula(mol),
            }
        else:
            # If conversion fails, initialize transformations with empty strings.
            transforms = {
                'INCHI': '',
                'INCHIKEY': '',
                'SMILES': '',
                'FORMULA': '',
            }

        # Calculate molecular masses (Exact Mass and Average Mass).
        if transforms:
            # Re-create the molecule object using the standardized INCHI or SMILES.
            if 'InChI=' in inchi_smiles:
                mol = Chem.MolFromInchi(transforms['INCHI'])
            else:
                mol = Chem.MolFromSmiles(transforms['SMILES'])

            if mol is not None:
                try:
                    # Calculate Exact Mass and Average Mass.
                    transforms['EXACTMASS'] = ExactMolWt(mol)
                    transforms['AVERAGEMASS'] = MolWt(mol)
                except:
                    # Handle errors during mass calculation by setting to empty strings.
                    transforms['EXACTMASS'] = ''
                    transforms['AVERAGEMASS'] = ''
                    return transforms
            else:
                # If molecule conversion for mass calculation fails, set to empty strings.
                transforms['EXACTMASS'] = ''
                transforms['AVERAGEMASS'] = ''

    return transforms


def map_transformations(row, unique_transforms):
    """
    Apply pre-calculated molecular transformations to a single row of the DataFrame.

    It first checks for 'INCHI', then for 'SMILES' in the 'unique_transforms'
    dictionary and updates the row with the pre-calculated values.

    :param row: A dictionary or Series representing a row of data.
    :type row: dict or pd.Series
    :param unique_transforms: A dictionary mapping unique InChI/SMILES strings
                              to their calculated chemical properties.
    :type unique_transforms: dict
    :return: The transformed row with updated chemical properties.
    :rtype: dict or pd.Series
    """
    # Get the original INCHI/SMILES, checking for NaN values.
    original_inchi = row['INCHI'] if pd.notna(row['INCHI']) else None
    original_smiles = row['SMILES'] if pd.notna(row['SMILES']) else None

    # Check if original INCHI is present in the pre-calculated transformations.
    if original_inchi and original_inchi in unique_transforms:
        # Update the row with the calculated properties.
        for key, value in unique_transforms[original_inchi].items():
            row[key] = value

    # If not found by INCHI, check if original SMILES is present.
    elif original_smiles and original_smiles in unique_transforms:
        # Update the row with the calculated properties.
        for key, value in unique_transforms[original_smiles].items():
            row[key] = value

    return row


def mols_derivation_and_calculation(CONCATENATE_DF, output_directory, progress_callback=None,
                                    total_items_callback=None, prefix_callback=None,
                                    item_type_callback=None):
    """
    Derives and calculates molecular properties (masses, standardized identifiers)
    for unique chemical structures (INCHI/SMILES) in the DataFrame.

    It uses callbacks for progress reporting during the process.

    :param CONCATENATE_DF: DataFrame containing 'INCHI' and 'SMILES' columns.
    :type CONCATENATE_DF: pd.DataFrame
    :param output_directory: Path to the directory where dropped rows will be saved.
    :type output_directory: str
    :param progress_callback: Function to update the progress. (Optional)
    :type progress_callback: function or None
    :param total_items_callback: Function to set the total number of items to process. (Optional)
    :type total_items_callback: function or None
    :param prefix_callback: Function to set the progress operation prefix. (Optional)
    :type prefix_callback: function or None
    :param item_type_callback: Function to specify the type of items being processed. (Optional)
    :type item_type_callback: function or None
    :return: A tuple containing:
             - The filtered DataFrame with calculated properties.
             - A DataFrame containing the rows that were dropped.
    :rtype: tuple[pd.DataFrame, pd.DataFrame]
    """

    # --- Step 1: Initialization for Progress Reporting ---

    if prefix_callback:
        prefix_callback("derivation and calculation:")

    if item_type_callback:
        item_type_callback("rows")

    # --- Step 2: Calculate Unique Transformations ---

    # Get unique, non-null INCHI and SMILES strings from the DataFrame.
    unique_inchi_smiles = pd.concat([CONCATENATE_DF['INCHI'],
                                     CONCATENATE_DF['SMILES']]).dropna().unique()

    # Set the total number of unique molecules for progress tracking.
    if total_items_callback:
        total_items_callback(len(unique_inchi_smiles), 0)

    # Process each unique string and store the transformations.
    processed_items = 0
    unique_transforms = {}

    for inchi_smiles in unique_inchi_smiles:
        unique_transforms[inchi_smiles] = apply_transformations(inchi_smiles)

        # Update progress for the calculation phase.
        processed_items += 1
        if progress_callback:
            progress_callback(processed_items)

    # --- Step 3: Map Transformations Back to DataFrame Rows ---

    if prefix_callback:
        prefix_callback("updating rows:")

    # Reset progress tracking for the mapping phase.
    results_processed = 0
    total_items = len(CONCATENATE_DF)

    if total_items_callback:
        total_items_callback(total_items, 0)

    def apply_row_mapping(row):
        """Helper function to map and report progress for each row."""
        nonlocal results_processed
        results_processed += 1

        # Report progress.
        if progress_callback:
            progress_callback(results_processed)

        # Apply transformations using the pre-calculated dictionary.
        return map_transformations(row, unique_transforms)

    # Apply the mapping function row-wise.
    CONCATENATE_DF = CONCATENATE_DF.apply(apply_row_mapping, axis=1)

    # --- Step 4: Validate INCHIKEY and Filter Rows ---

    # Create a boolean mask to check if 'INCHIKEY' fully matches the expected pattern.
    mask = CONCATENATE_DF['INCHIKEY'].str.fullmatch(scripts.globals_vars.inchikey_pattern,
                                                    na=False)

    # Filter the DataFrame, retaining only rows with a valid INCHIKEY.
    CONCATENATE_DF = CONCATENATE_DF[mask]

    # Store the row count before dropping nulls for deletion reporting.
    before = len(CONCATENATE_DF)

    # Define critical columns that must have non-null values.
    critical_columns = ['EXACTMASS', 'AVERAGEMASS', 'SMILES', 'INCHI', 'INCHIKEY']

    # Identify rows that have at least one null value in the critical columns.
    rows_to_drop = CONCATENATE_DF[CONCATENATE_DF[critical_columns].isnull().any(axis=1)]

    # Filter the DataFrame by dropping rows with nulls in critical columns.
    CONCATENATE_DF = CONCATENATE_DF.dropna(subset=critical_columns)

    # --- Step 5: Deletion Reporting and File Output ---

    # Add a reason for the deletion to the dropped rows.
    rows_to_drop['DELETION_REASON'] = ("spectrum deleted because it has neither inchi "
                                        "nor smiles nor inchikey, even after re calculation")

    # Ensure the target directory for deletions exists.
    deletion_dir = os.path.join(output_directory, "DELETED_SPECTRUMS")

    # Define file name and full path for the deleted spectra report.
    deleted_file_path = os.path.join(deletion_dir,
                                     "deleted_no_inchi_smiles_inchikey_after_re_calculation.csv")

    # Write the dropped rows to a tab-separated CSV file.
    rows_to_drop.to_csv(deleted_file_path, index=False, sep='\t', encoding='utf-8')

    # Calculate and report the number of missing rows (deleted).
    after = len(CONCATENATE_DF)
    missing = before - after
    scripts.deletion_report.no_smiles_no_inchi_no_inchikey += missing

    # Return the processed DataFrame.
    return CONCATENATE_DF