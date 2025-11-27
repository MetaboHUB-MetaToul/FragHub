from scripts.peaks_filters.check_minimum_of_high_peaks_requiered import *
from scripts.peaks_filters.remove_peak_above_precursormz import *
from scripts.peaks_filters.check_minimum_peak_requiered import *
from scripts.peaks_filters.normalize_intensity import *
from scripts.peaks_filters.keep_mz_in_range import *
from scripts.peaks_filters.reduce_peak_list import *
import scripts.deletion_report
from numba import jit
import numpy as np


@jit(nopython=True, nogil=True)
def remove_non_positive_peaks(peak_array: np.ndarray) -> np.ndarray:
    """
    Removes peaks whose intensity is less than or equal to zero.

    This function is optimized for speed using Numba (jit).

    :param peak_array: A NumPy array containing peak data. The second column
                       (index 1) must contain the peak intensities.
    :type peak_array: np.ndarray
    :return: The filtered NumPy array including only peaks with strictly positive intensity.
    :rtype: np.ndarray
    """
    # Keep only rows where the value in the second column (intensity) is > 0
    return peak_array[peak_array[:, 1] > 0]


def apply_filters(spectrum, peak_array, precursormz, parameters_dict):
    """
    Applies a sequence of mass spectrometry peak list filters based on the
    provided configuration dictionary.

    The application order is critical for the intended processing logic:
    1. Remove non-positive peaks
    2. Check minimum required peaks (count)
    3. Remove peaks above the precursor m/z
    4. Reduce peak list (max number of peaks)
    5. Normalize intensity
    6. Keep peaks within a user-defined m/z range
    7. Check minimum number of high-intensity peaks

    :param spectrum: The spectrum object/dictionary (used for logging deletions).
    :param peak_array: The input NumPy array [m/z, intensity] containing peak information.
    :type peak_array: np.ndarray
    :param precursormz: The precursor m/z value, used for one specific filter.
    :type precursormz: float or None
    :param parameters_dict: A dictionary containing filtering flags (1.0 or 0.0)
                            and their respective parameter values.
    :type parameters_dict: dict
    :return: The filtered NumPy array [m/z, intensity] or an empty array if
             a critical filter caused all peaks to be removed.
    :rtype: np.ndarray
    """
    # Retrieve filtering parameters from the configuration dictionary
    n_peaks = parameters_dict['check_minimum_peak_requiered_n_peaks']
    max_peaks = parameters_dict['reduce_peak_list_max_peaks']
    mz_from = parameters_dict['keep_mz_in_range_from_mz']
    mz_to = parameters_dict['keep_mz_in_range_to_mz']
    intensity_percent = parameters_dict['check_minimum_of_high_peaks_requiered_intensity_percent']
    no_peaks = parameters_dict['check_minimum_of_high_peaks_requiered_no_peaks']

    # --- Step 1: Mandatory filter to remove invalid intensity peaks ---
    peak_array = remove_non_positive_peaks(peak_array)

    # --- Step 2: Apply conditional filters in sequence ---

    # Filter 1: Check minimum required peak count
    if parameters_dict['check_minimum_peak_requiered'] == 1.0:
        peak_array = check_minimum_peak_requiered(spectrum, peak_array, n_peaks)
        if peak_array.size == 0:
            return np.empty((0, 2), dtype=np.float64)

    # Filter 2: Remove peaks above precursor m/z
    if parameters_dict['remove_peak_above_precursormz'] == 1.0 and precursormz is not None:
        peak_array = remove_peak_above_precursormz(peak_array, precursormz)
        if peak_array.size == 0:
            # Log deletion reason and update report
            spectrum['DELETION_REASON'] = "spectrum deleted because peaks list is empty after removing peaks above precursor m/z"
            scripts.deletion_report.deleted_spectrum_list.append(spectrum)
            scripts.deletion_report.all_peaks_above_precursor_mz += 1
            return np.empty((0, 2), dtype=np.float64)

    # Filter 3: Reduce peak list to a maximum number of peaks
    if parameters_dict['reduce_peak_list'] == 1.0:
        peak_array = reduce_peak_list(peak_array, max_peaks)

    # Filter 4: Normalize peak intensity (sets maximum intensity to 1.0)
    if parameters_dict['normalize_intensity'] == 1.0:
        peak_array = normalize_intensity(peak_array)
        if peak_array.size == 0:
            return np.empty((0, 2), dtype=np.float64)

    # Filter 5: Keep peaks within a user-defined m/z range
    if parameters_dict['keep_mz_in_range'] == 1.0:
        peak_array = keep_mz_in_range(peak_array, mz_from, mz_to)
        if peak_array.size == 0:
            # Log deletion reason and update report
            spectrum['DELETION_REASON'] = "spectrum deleted because peaks list is empty after removing peaks out of mz range choiced by the user"
            scripts.deletion_report.deleted_spectrum_list.append(spectrum)
            scripts.deletion_report.no_peaks_in_mz_range += 1
            return np.empty((0, 2), dtype=np.float64)

    # Filter 6: Check minimum number of high-intensity peaks required
    if parameters_dict['check_minimum_of_high_peaks_requiered'] == 1.0:
        peak_array = check_minimum_of_high_peaks_requiered(peak_array, intensity_percent, no_peaks)
        if peak_array.size == 0:
            # Log deletion reason and update report
            spectrum['DELETION_REASON'] = "spectrum deleted because peaks list does not contain minimum number of high peaks required according to the value choiced by the user"
            scripts.deletion_report.deleted_spectrum_list.append(spectrum)
            return np.empty((0, 2), dtype=np.float64)

    # Return the final filtered peak array
    return peak_array