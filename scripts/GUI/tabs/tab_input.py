from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QLabel,
    QHBoxLayout, QComboBox, QFileDialog
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize, Qt
from scripts.GUI.utils.global_vars import parameters_dict
import os
import sys


# Determine the base directory for resource files, handling PyInstaller executable or script execution.
if getattr(sys, 'frozen', False):
    # Base directory when running as a frozen executable.
    BASE_DIR = sys._MEIPASS
else:
    # Base directory when running as a Python script.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class InputTab(QWidget):
    """
    GUI tab for selecting input files (json, csv, msp, mgf).
    It manages the file selection button and displays selected files in a dropdown.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.file_menu = None

        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        """Sets up the layout and widgets for the Input Tab."""

        # Spacer to push content to the vertical center.
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- File Selection Button ---
        button = QPushButton()
        # Load the icon from the assets directory.
        icon_path = os.path.join(BASE_DIR, './GUI/assets/files_icon.png')
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(128, 128))
        button.setFixedSize(140, 140)
        # Connect the click event to the file browsing handler.
        button.clicked.connect(self.browse_files)

        # Layout to center the button horizontally.
        button_layout = QHBoxLayout()
        button_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(button_layout)

        # --- Label below the button ---
        label = QLabel("Select input files")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(label)

        # --- Dropdown Menu for selected files ---
        self.file_menu = QComboBox()
        self.file_menu.setFixedWidth(200)
        self.file_menu.setPlaceholderText("No files selected")
        self.layout.addWidget(self.file_menu, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacer to push the info button down.
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Info button in the bottom right ---
        info_button_layout = QHBoxLayout()
        # Spacer to push the info button to the right.
        info_button_layout.addSpacerItem(
            QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )

        info_button = QPushButton("🛈")
        info_button.setFixedSize(30, 30)
        info_button.setToolTip(
            "Select single or multiple .json, .csv, .msp, or .mgf files"
        )
        info_button_layout.addWidget(info_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout.addLayout(info_button_layout)

    def browse_files(self):
        """
        Opens a file dialog for the user to select one or multiple input files.
        Updates the global parameters and the file list dropdown upon successful selection.
        """
        # Start the dialog from the machine's root directory.
        start_directory = os.path.abspath(os.sep)

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose files",
            start_directory,
            # File filter can be added here if needed, but omitted for maximum flexibility:
            # "Mass Spectrometry Files (*.json *.csv *.msp *.mgf)"
        )

        if files:
            # Update the global dictionary with the full list of selected file paths.
            parameters_dict["input_directory"] = files

            # Populate the dropdown menu with only the base names of the files.
            self.file_menu.clear()
            for file_path in files:
                basename = os.path.basename(file_path)
                self.file_menu.addItem(basename)

            # Set the dropdown to display the first selected file.
            self.file_menu.setCurrentText(os.path.basename(files[0]))