import os
import sys
from threading import Thread

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTabWidget,
    QMessageBox, QApplication, QStackedWidget
)
from PyQt6.QtGui import QFont, QPixmap, QIcon
from PyQt6.QtCore import Qt, pyqtSignal

# Import application logic and GUI components.
from ..main_worker import run_main_in_worker
from .error_handler import show_error_message
from .tabs.tab_input import InputTab
from .tabs.tab_output import OutputTab
from .tabs.tab_filters import FiltersTab
from .tabs.tab_de_novo import DeNovoTab
from .tabs.tab_output_settings import OutputSettingTab
from .tabs.tab_projects import ProjectsTab
from .progress_window import ProgressView
from .utils.global_vars import parameters_dict


# Determine the base directory for resource files, handling PyInstaller executable or script execution.
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    # Base directory when running as a Python script.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class MainWindow(QMainWindow):
    """
    The main window for the FragHub GUI application. It uses a QStackedWidget
    to switch between the configuration view (tabs) and the progress view.
    """
    # Signal emitted when an execution error occurs in the worker thread.
    error_occurred_signal = pyqtSignal(str)
    # Signal emitted when the worker thread task successfully finishes or is stopped.
    task_finished_signal = pyqtSignal()

    def __init__(self, main_function_ref):
        super().__init__()

        # Set the main window icon for the taskbar.
        icon_path = os.path.join(BASE_DIR, "GUI", "assets", "FragHub_icon.png")
        self.setWindowIcon(QIcon(icon_path))

        # Set window flags to allow minimization and closing, but not resizing.
        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint
        )
        self.main_function = main_function_ref
        self.setWindowTitle("FragHub 1.4.1")
        self.setGeometry(100, 100, 1280, 720)

        # QStackedWidget to manage different views (config vs. progress).
        self.stacked_widget = QStackedWidget()

        # 1. Configuration View (Index 0): Contains all setting tabs.
        self.config_view = self._create_config_view()
        self.stacked_widget.addWidget(self.config_view)

        # 2. Progress View (Index 1): Displays real-time execution status.
        self.progress_view = ProgressView()
        self.stacked_widget.addWidget(self.progress_view)

        # Connect signals for managing the worker thread from the progress view.
        self.progress_view.stop_requested_signal.connect(self.handle_stop_request)
        self.progress_view.finish_requested_signal.connect(lambda: self.clean_exit(force_quit_app=False))

        self.setCentralWidget(self.stacked_widget)
        self.show_config_view()

        # Thread and state management variables.
        self.running = False
        self.thread = None
        self.stop_thread_flag = False

        # Connect internal signals to their handlers.
        self.error_occurred_signal.connect(self.handle_execution_error)
        self.task_finished_signal.connect(self.handle_task_finished)

    def _create_config_view(self):
        """Creates and returns the widget containing all configuration tabs and the START button."""
        config_container = QWidget()
        main_layout = QVBoxLayout(config_container)

        # --- Application Banner ---
        banner = QLabel()
        icon_path = os.path.join(BASE_DIR, "GUI", "assets", "FragHub_icon.png")
        pixmap = QPixmap(icon_path)

        if not pixmap.isNull():
            # Scale the icon for the banner.
            pixmap_scaled = pixmap.scaled(
                200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            banner.setPixmap(pixmap_scaled)

        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(banner)

        # --- Tab Widget for Configuration ---
        self.tabs = QTabWidget()
        self.input_tab = InputTab()
        self.output_tab = OutputTab()
        self.filters_tab = FiltersTab()
        self.denovo_tab = DeNovoTab()
        self.output_settings_tab = OutputSettingTab()
        self.projects_tab = ProjectsTab()

        self.tabs.addTab(self.input_tab, "INPUT")
        self.tabs.addTab(self.output_tab, "OUTPUT")
        self.tabs.addTab(self.filters_tab, "Filters settings")
        self.tabs.addTab(self.denovo_tab, "De Novo settings")
        self.tabs.addTab(self.output_settings_tab, "Output settings")
        self.tabs.addTab(self.projects_tab, "Projects settings")
        main_layout.addWidget(self.tabs)

        # Connect the output directory selection to the project tab to check for `.fraghub` file.
        self.output_tab.output_directory_changed.connect(
            self.projects_tab.output_directory_changed_signal
        )

        # --- START Button ---
        self.start_button = QPushButton("START")
        self.start_button.setFixedSize(140, 60)
        self.start_button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.start_button.clicked.connect(self.open_progress_window)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        return config_container

    def show_config_view(self):
        """Switches the QStackedWidget to the configuration view (Index 0)."""
        # Reset the progress view state before returning to config.
        if self.progress_view:
            self.progress_view.reset_view()

        self.stacked_widget.setCurrentIndex(0)
        self.setEnabled(True)
        self.start_button.setEnabled(True)

    def show_progress_view(self):
        """Switches the QStackedWidget to the progress view (Index 1)."""
        self.stacked_widget.setCurrentIndex(1)
        self.setEnabled(True)

    def open_progress_window(self):
        """
        Checks for mandatory input/output selections before starting execution.
        If selections are valid, switches to the progress view and starts the worker thread.
        """
        # Check for mandatory selections from the global parameters.
        input_files = parameters_dict.get("input_directory")
        output_dir = parameters_dict.get("output_directory")

        missing_selections = []
        if not input_files:
            missing_selections.append("at least one input file")
        if not output_dir:
            missing_selections.append("an output directory")

        if missing_selections:
            # Display a warning if selections are missing.
            message = "Please select " + " and ".join(missing_selections) + " before starting."
            QMessageBox.warning(self, "Selection Required", message)
            return

        if not self.running:
            self.show_progress_view()
            self.start_execution()

    def handle_stop_request(self):
        """Sets the flag to signal the worker thread to stop execution."""
        if self.running:
            self.stop_thread_flag = True

    def start_execution(self):
        """Initializes the worker thread and starts the main processing function."""
        if self.running:
            return

        self.running = True
        self.stop_thread_flag = False

        # Reset thread if it was previously active.
        if self.thread and self.thread.is_alive():
            self.stop_thread_flag = True
            self.thread.join()
            self.thread = None

        # Initialize progress bar display.
        if self.progress_view:
            self.progress_view.progress_bar_widget.update_total_items(total=100, completed=0)
            self.progress_view.progress_bar_widget.update_progress_bar(0)

        # Define callback functions for the worker to communicate with the GUI.
        callbacks = {
            'progress': self.progress_view.update_progress_signal.emit,
            'total_items': self.progress_view.update_total_signal.emit,
            'prefix': self.progress_view.update_prefix_signal.emit,
            'item_type': self.progress_view.update_item_type_signal.emit,
            'step': self.progress_view.update_step_signal.emit,
            'completion': self.progress_view.completion_callback.emit,
            'deletion': self.progress_view.deletion_callback.emit
        }
        # Define internal signals for the worker to communicate its state.
        signals = {'error': self.error_occurred_signal, 'finished': self.task_finished_signal}
        # Provide a function to check the stop status.
        stop_flag_provider = lambda: self.stop_thread_flag

        # Start the worker thread.
        self.thread = Thread(
            target=run_main_in_worker,
            args=(self.main_function, callbacks, signals, stop_flag_provider),
            daemon=True,
            name="MainWorkerThread_FragHub"
        )
        self.thread.start()

    def handle_task_finished(self):
        """Resets state variables and manages view switching after thread completion."""
        self.running = False
        self.thread = None
        # Return to configuration view if the task was stopped by the user.
        if self.stop_thread_flag:
            self.show_config_view()
        self.stop_thread_flag = False

    def handle_execution_error(self, traceback_str):
        """
        Displays a detailed error message and returns to the configuration view
        after the user closes the error dialog.
        """
        # Use the custom error handler with a callback to return to config view.
        show_error_message(
            parent=self,
            title="Execution Error",
            message=traceback_str,
            on_close=lambda: self.clean_exit(force_quit_app=False)
        )

    def clean_exit(self, force_quit_app=True):
        """
        Gracefully stops the worker thread and either quits the application
        or returns to the configuration view.
        """
        # Request thread stop and wait for it to join if running.
        if self.running and self.thread and self.thread.is_alive():
            self.stop_thread_flag = True
            self.thread.join(timeout=3.0)

        self.running = False
        if force_quit_app:
            # Terminate the application entirely.
            QApplication.instance().quit()
        else:
            # Return to the configuration view.
            self.show_config_view()

    def closeEvent(self, event):
        """
        Handles the main window close event, asking for confirmation if a process is running.
        """
        if self.running:
            reply = QMessageBox.question(
                self, 'Quit FragHub?',
                "A process is running. Are you sure you want to quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clean_exit(force_quit_app=True)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()