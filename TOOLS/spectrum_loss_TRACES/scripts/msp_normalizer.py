from normalizer.values_normalizer import *
from set_parameters import parameters_dict
from peaks_filters.filters import *
import concurrent.futures
from tqdm import tqdm
import numpy as np
import re

np.set_printoptions(suppress=True)

global float_check_pattern
float_check_pattern = re.compile(r"(-?\d+[.,]?\d*(?:[Ee][+-]?\d+)?)")

def peak_list_to_np_array(peak_list, precursormz, minimum_peaks_not_requiered):
    """
    This function serves the purpose of converting a list of peak tuples (mz and intensity values) into a numpy array.

    :param peak_list: A list of tuples. Each tuple represents a peak and it contains mz value and intensity of the peak.
    :param precursormz: The precursor mz value for the peaks.

    :return: The function returns a numpy array that represents the peaks.
             The peaks in the returned numpy array are sorted by their mz values.
             The peaks are also filtered based on the precursor mz value.
    """

    # Convert the list of tuples (peak_list) to a numpy array.
    # Each tuple in the list contains two floating point values - mz value and intensity of a peak.
    peak_list = np.array(peak_list, dtype=float)

    # Sort the numpy array of peaks based on the mz values.
    # The mz values are the first value in each tuple, hence located in the first column of the array.
    # Method np.argsort() returns indices that sort the mz values.
    # By indexing the original array with these indices, we get sorted array.
    peak_list = peak_list[peak_list[:, 0].argsort()]

    # Apply appropriate set of filters to the sorted numpy array of peaks.
    # The filters use the precursor mz value and pre-defined parameters.
    peak_list, minimum_peaks_not_requiered = apply_filters(peak_list, precursormz, parameters_dict, minimum_peaks_not_requiered)

    # Return the sorted and preset-filtered numpy array of peaks.
    return peak_list, minimum_peaks_not_requiered

def peak_list_to_str(peak_list_np):
    """
    This function converts a peak list numpy array into a string format. Each peak is represented as a space-separated
    string of floating point values, and each peak is separated by a newline.

    :param peak_list_np: The peak list represented as a numpy array. The numpy array is expected to contain floating-point values.
    :return: A string representation of the peak list where each row represents a peak and is formatted as a space-separated
    string of floating-point values.
    """
    # Convert the peak list numpy array to a list of lists. Each sub-list contains floating point values representing a peak.
    # The numpy round function is used to limit the precision of the floating-point values to 8 decimal places.
    peak_list_np = peak_list_np.round(8).tolist()

    # Convert the list of lists into a string format. Each sub-list (representing a peak) is converted into a space-separated
    # string of floats. Sub-lists are then joined together with newline characters to form the final string.
    #
    # The join function is used twice:
    # 1) The inner join function is used to convert each sub-list into a space-separated string of floats.
    #    The string formatter is used to ensure each float is represented to 8 decimal places.
    # 2) The outer join function is used to join together all the space-separated strings (representing peaks) with newline characters.
    peak_list_np = "\n".join(" ".join(f"{val:.8f}" for val in sublist) for sublist in peak_list_np)

    # Return the final string representation of the peak list.
    return peak_list_np

def spectrum_cleaning(spectrum):
    """
    This function cleans the input 'spectrum'.

    It starts by checking if the 'PEAKS_LIST' attribute of the spectrum exists.
    If it does, it continues with normalizing all key-values in the spectrum.
    After normalization, the function checks if the 'PRECURSORMZ' exists in the spectrum and a regular expression search for
    the 'float_check_pattern' in the 'PRECURSORMZ' key returns a match.
    If both conditions are true, it modifies 'PRECURSORMZ' to match the regex group, converts it to float and replaces any commas with periods.
    If the float value is positive, it proceeds to convert the peak list to a numpy array and then to string,
    subsequently updating the spectrum's 'PEAKS_LIST' and 'NUM PEAKS' attributes.

    :param spectrum: dictionary containing spectrum information
    :return: cleaned spectrum dictionary if it passes all checks, otherwise None
    """
    no_smiles_no_inchi = 0
    no_or_bad_precursormz_and_no_or_bad_addcut = 0
    no_peaks_list = 0
    minimum_peaks_not_requiered = 0

    peak_list = spectrum["PEAKS_LIST"]
    # If peak_list is not present in the spectrum dictionary, it returns None
    if not peak_list:
        no_peaks_list = 1
        return None, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered
    spectrum, no_smiles_no_inchi = normalize_values(spectrum, no_smiles_no_inchi)
    # If normalization of spectrum fails, it returns None
    if not spectrum:
        return None, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered
    # Checks if "PRECURSORMZ" exists in the spectrum
    if "PRECURSORMZ" in spectrum:
        if re.search(float_check_pattern, str(spectrum["PRECURSORMZ"])):
            # 'PRECURSORMZ' modification with match from a regular expression search for 'float_check_pattern'
            spectrum["PRECURSORMZ"] = re.search(float_check_pattern, str(spectrum["PRECURSORMZ"])).group(1)
            float_precursor_mz = float(spectrum["PRECURSORMZ"].replace(",", "."))
            # Float value of 'PRECURSORMZ' needs to be greater than 0
            if float_precursor_mz <= 0.0:
                no_or_bad_precursormz_and_no_or_bad_addcut = 1
                return None, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered
            # Converts peak list to a numpy array
            peak_list_np, minimum_peaks_not_requiered = peak_list_to_np_array(peak_list, float_precursor_mz, minimum_peaks_not_requiered)
            # If numpy array is empty, it returns none
            if peak_list_np.size == 0:
                return None, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered
            spectrum["NUM PEAKS"] = str(peak_list_np.shape[0])
            # Convert numpy array back to string and update 'PEAKS_LIST' in spectrum
            peak_list_np = peak_list_to_str(peak_list_np)
            spectrum["PEAKS_LIST"] = peak_list_np
            return spectrum, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered
        else:
            no_or_bad_precursormz_and_no_or_bad_addcut = 1
            return None, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered
    return spectrum, no_smiles_no_inchi, no_or_bad_precursormz_and_no_or_bad_addcut, no_peaks_list, minimum_peaks_not_requiered

def spectrum_cleaning_processing(spectrum_list):
    """
    Main function used for performing spectrum cleaning operation on multiple spectrums.

    This function uses the concurrent.futures module to perform cleaning operation on multiple spectrums concurrently.
    The spectrum list is divided into chunks of determined size. Each chunk is then processed concurrently by utilizing
    the ThreadPoolExecutor.

    During the operation, a progress bar is shown to indicate the progress of the operation. The progress bar is updated
    every time a chunk of spectrums has been processed.

    Finally, the cleaned spectrums are collected and returned.

    :param spectrum_list: A list of spectrums that need to be cleaned
    :type spectrum_list: list
    :return: A list of cleaned spectrums
    :rtype: list
    """

    # Define the chunk size: the number of spectrums that can be processed at once
    chunk_size = 5000
    # Initialize the list that will hold the cleaned spectra
    final = []
    # Initialize a progress bar to monitor the processing
    progress_bar = tqdm(total=len(spectrum_list), unit=" spectrums", colour="green", desc="{:>70}".format("cleaning spectrums"))
    # Loop over the spectrum list using the defined chunk size
    for i in range(0, len(spectrum_list), chunk_size):
        # Create a ThreadPoolExecutor for concurrent processing
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Extract a chunk of spectrum from the spectrum list
            chunk = spectrum_list[i:i + chunk_size]
            # Execute the spectrum_cleaning function on each spectrum from the chunk concurrently
            results = list(executor.map(spectrum_cleaning, chunk))
            # Update the progress bar
            progress_bar.update(len(chunk))
        # Collect all non-None cleaned spectrums from the chunk and append them to the final cleaned spectrum list
        final.extend([res for res in results if res is not None])
    # Close the progress bar after all has been processed
    progress_bar.close()
    return final  # Return the cleaned spectrum list