from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSpacerItem, QSizePolicy, QLabel,
    QHBoxLayout, QFileDialog
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QSize, Qt, pyqtSignal
import sys
import os
from scripts.backend_vars import parameters_dict


# Determine the base directory for resource files, handling PyInstaller executable or script execution.
if getattr(sys, 'frozen', False):
    # Base directory when running as a frozen executable.
    BASE_DIR = sys._MEIPASS
else:
    # Base directory when running as a Python script.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class OutputTab(QWidget):
    """
    GUI tab for selecting the output directory where processed files will be saved.
    It manages the directory selection button and displays the selected path.
    """
    # Signal emitted when the output directory path changes.
    output_directory_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.path_label = None

        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        """Sets up the layout and widgets for the Output Tab."""

        # Spacer to push content to the vertical center.
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Directory Selection Button ---
        button = QPushButton()
        # Load the directory icon from assets.
        icon_path = os.path.join(BASE_DIR, './GUI/assets/directory.png')
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(128, 128))
        button.setFixedSize(140, 140)
        # Connect the click event to the directory browsing handler.
        button.clicked.connect(self.browse_output_files)

        # Layout to center the button horizontally.
        button_layout = QHBoxLayout()
        button_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(button_layout)

        # --- Label below the button ---
        label = QLabel("Select output directory")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(label)

        # --- Label to display the selected folder path ---
        self.path_label = QLabel("No directory selected")
        self.path_label.setFont(QFont("Arial", 10))
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Allow the long path string to wrap onto multiple lines.
        self.path_label.setWordWrap(True)
        self.layout.addWidget(self.path_label)

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
            "Create a new empty directory or Select an existing directory "
            "where FragHub has already written files"
        )
        info_button_layout.addWidget(info_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.layout.addLayout(info_button_layout)

    def browse_output_files(self):
        """
        Opens a directory dialog for the user to select an output location.
        Updates the global parameters and the display label upon selection.
        """
        # Start the dialog from the machine's root directory.
        start_directory = os.path.abspath(os.sep)

        directory = QFileDialog.getExistingDirectory(
            self,
            "Choose a directory for OUTPUT",
            start_directory
        )

        if directory:
            # Update the global dictionary with the selected path.
            parameters_dict["output_directory"] = directory
            # Emit a signal with the new directory path.
            self.output_directory_changed.emit(directory)

            # Update the label to display the selected path to the user.
            self.path_label.setText(directory)