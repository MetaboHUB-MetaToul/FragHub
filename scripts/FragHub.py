import sys
import os
import ctypes
import time
import platform
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import pyqtSignal, QObject, QThread

from scripts.GUI.error_handler import exception_hook
from scripts.GUI.splash_screen import LoadingSplashScreen
from scripts.GUI.main_GUI import MainWindow


# Determine the base directory for resource files, handling PyInstaller executable or script execution.
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    # Base directory when running as a Python script.
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Set the application model ID for better integration on Windows.
if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FragHub")


class StartupWorker(QObject):
    """
    QObject worker running asynchronous startup tasks, such as module imports,
    to prevent blocking the GUI thread.
    """
    # Signal emitted upon successful completion, carrying the main function reference.
    finished = pyqtSignal(object)
    # Signal emitted on error, carrying the traceback message.
    error = pyqtSignal(str)
    # Signal to update the splash screen message.
    update_splash_message = pyqtSignal(str, int)

    def __init__(self, base_dir):
        super().__init__()
        self._base_dir = base_dir

    def run_startup_tasks(self):
        """
        Executes required startup tasks, including importing the main processing function.
        """
        try:
            self.update_splash_message.emit("Loading FragHub, please wait...", 20)
            time.sleep(1)

            # Dynamically import the core application entry point.
            # Assuming 'scripts.MAIN' contains the 'MAIN' function.
            from scripts.MAIN import MAIN as imported_main

            self.update_splash_message.emit("Initializing main window", 20)
            time.sleep(1)

            # Emit the main function reference upon success.
            self.finished.emit(imported_main)

        except ImportError as e:
            # Handle import failures, providing detailed traceback.
            self.error.emit(f"Failed to import 'scripts.MAIN': {e}\n{traceback.format_exc()}")
        except Exception as e:
            # Handle any other unexpected exceptions.
            self.error.emit(f"Unexpected error during startup tasks: {e}\n{traceback.format_exc()}")


def run_gui():
    """Initializes the Qt application, configures the exception hook, and runs the GUI."""

    # Add the 'scripts' directory to sys.path to resolve internal imports.
    scripts_path = os.path.join(BASE_DIR, 'scripts')
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)

    # Set the global exception handler for unhandled exceptions.
    sys.excepthook = exception_hook
    # Create the QApplication instance.
    app = QApplication(sys.argv if hasattr(sys, 'argv') else [''])

    # --- Application Icon Setup ---
    scripts_gui_assets = os.path.join(BASE_DIR, "GUI", "assets")
    # Choose specific icon format based on the operating system.
    if platform.system() == "Darwin":
        app_icon_path = os.path.join(BASE_DIR, scripts_gui_assets, "FragHub_Python_icon.icns")
    else:
        app_icon_path = os.path.join(BASE_DIR, scripts_gui_assets, "FragHub_Python_icon.ico")
    # Fallback to PNG if the specific icon format is not found.
    if not os.path.exists(app_icon_path):
        app_icon_path = os.path.join(BASE_DIR, scripts_gui_assets, "FragHub_icon.png")

    if os.path.exists(app_icon_path):
        app.setWindowIcon(QIcon(app_icon_path))

    # --- Splash Screen Setup ---
    splash_pix_path = os.path.join(BASE_DIR, scripts_gui_assets, "FragHub_icon.png")
    splash_pixmap = QPixmap(splash_pix_path)
    # Instantiate and show the custom loading splash screen.
    splash = LoadingSplashScreen(splash_pixmap)
    splash.show_message("Loading FragHub...")
    splash.show()

    # --- Startup Thread Management ---
    startup_thread = QThread()
    startup_worker = StartupWorker(BASE_DIR)
    startup_worker.moveToThread(startup_thread)

    # Shared dictionary to hold references updated across threads.
    shared_state = {'main_window': None, 'main_function': None, 'splash_screen': splash}

    def on_startup_complete(imported_main_function):
        """Handler for successful startup: creates and shows the main window."""
        if not QApplication.instance():
            return

        shared_state['main_function'] = imported_main_function
        try:
            # Create the main window, passing the core function reference.
            shared_state['main_window'] = MainWindow(main_function_ref=shared_state['main_function'])
            shared_state['main_window'].show()
        except Exception as e:
            # Handle error during main window creation.
            on_startup_error(f"Failed to create main window: {e}\n{traceback.format_exc()}")
            return

        # Close and dereference the splash screen.
        if shared_state['splash_screen']:
            shared_state['splash_screen'].close()
            shared_state['splash_screen'] = None

    def on_startup_error(error_message):
        """Handler for critical errors: closes splash and displays a fatal error message."""
        if shared_state['splash_screen']:
            shared_state['splash_screen'].close()
            shared_state['splash_screen'] = None

        # Display error via a modal message box.
        QMessageBox.critical(None, "Fatal Startup Error", f"Could not start FragHub:\n{error_message}")

        if QApplication.instance():
            QApplication.instance().quit()

    def update_splash(message, font_size=12):
        """Updates the message on the splash screen."""
        if shared_state['splash_screen']:
            shared_state['splash_screen'].show_message(message, font_size=font_size)

    # --- Signal and Slot Connections ---
    startup_thread.started.connect(startup_worker.run_startup_tasks)
    startup_worker.finished.connect(on_startup_complete)
    startup_worker.error.connect(on_startup_error)
    startup_worker.update_splash_message.connect(update_splash)

    # Cleanup connections for safe thread termination.
    startup_worker.finished.connect(startup_thread.quit)
    startup_worker.error.connect(startup_thread.quit)
    startup_worker.finished.connect(startup_worker.deleteLater)
    startup_worker.error.connect(startup_worker.deleteLater)
    startup_thread.finished.connect(startup_thread.deleteLater)

    # Start the worker thread and the main application event loop.
    startup_thread.start()
    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    run_gui()