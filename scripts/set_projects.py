from scripts.GUI.utils.global_vars import parameters_dict
import json
import os


def remove_files(directory):
    """
    Recursively removes all files (excluding files like '.gitkeep', though
    not explicitly checked here, the original logic removes all files) in the
    given directory and its subdirectories.

    :param directory: The starting directory path.
    :type directory: str
    :return: None
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            remove_files(file_path)


def reset_updates(output_directory):
    """
    Resets project updates and output files by deleting the 'updates.json'
    file and recursively removing all files within the output directory.

    :param output_directory: The output directory path where the project files reside.
    :type output_directory: str
    :return: None
    """
    json_update_path = os.path.join(output_directory, "updates.json")
    output_path = output_directory

    # Delete the updates.json file if it exists
    if os.path.exists(json_update_path):
        os.remove(json_update_path)

    # Recursively remove all output files
    if os.path.exists(output_path):
        remove_files(output_path)


def init_project(output_directory):
    """
    Initializes the necessary directory structure and control files for a new project.

    This includes creating the output directory, essential subdirectories (CSV/JSON/MSP
    for POS/NEG modes), the 'DELETED_SPECTRUMS' directory, and control files
    ('.fraghub' and 'updates.json').

    :param output_directory: The base directory path for the new project.
    :type output_directory: str
    :return: None
    """

    # Define paths for control files
    updates_file_path = os.path.join(output_directory, "updates.json")
    fraghub_file_path = os.path.join(output_directory, ".fraghub")

    # Define required directory structure
    main_directories = ['CSV', 'JSON', 'MSP']
    sub_directories = ['NEG', 'POS']

    # Create the base output directory if it does not exist
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    # Create the 'updates.json' file with an empty JSON object if it does not exist
    if not os.path.isfile(updates_file_path):
        with open(updates_file_path, 'w') as fp:
            json.dump({}, fp)

    # Create an empty '.fraghub' project file if it does not exist
    if not os.path.isfile(fraghub_file_path):
        with open(fraghub_file_path, 'w') as fp:
            pass

    # Create the main and subdirectories (e.g., CSV/NEG, JSON/POS)
    for main_dir in main_directories:
        for sub_dir in sub_directories:
            dir_path = os.path.join(output_directory, main_dir, sub_dir)
            if not os.path.isdir(dir_path):
                os.makedirs(dir_path)

    # Create the dedicated directory for deleted spectra reports
    deleted_spectrums_dir = os.path.join(output_directory, "DELETED_SPECTRUMS")
    if not os.path.isdir(deleted_spectrums_dir):
        os.makedirs(deleted_spectrums_dir)