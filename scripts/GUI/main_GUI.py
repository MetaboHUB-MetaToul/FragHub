import os
import sys
from threading import Thread

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTabWidget, QMessageBox, QApplication,
    QStackedWidget  # QStackedWidget AJOUTÉ
)
from PyQt6.QtGui import QFont, QPixmap, QIcon  # QIcon AJOUTÉ
from PyQt6.QtCore import Qt, pyqtSignal

# FIX: Updated relative and absolute imports
from ..main_worker import run_main_in_worker
from .error_handler import show_error_message
from .tabs.tab_input import InputTab
from .tabs.tab_output import OutputTab
from .tabs.tab_filters import FiltersTab
from .tabs.tab_de_novo import DeNovoTab
from .tabs.tab_output_settings import OutputSettingTab
from .tabs.tab_projects import ProjectsTab
from .progress_window import ProgressView  # ProgressWindow changé en ProgressView
# --- ADDITION ---
# Import the global dictionary to check selections
from .utils.global_vars import parameters_dict

# --- END OF ADDITION ---

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    # FIX: Go up 2 levels (GUI -> scripts -> root)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class MainWindow(QMainWindow):
    error_occurred_signal = pyqtSignal(str)
    task_finished_signal = pyqtSignal()

    def __init__(self, main_function_ref):
        super().__init__()

        # AJOUT : Définir l'icône de la fenêtre principale (pour la barre des tâches)
        icon_path = os.path.join(BASE_DIR, "GUI", "assets", "FragHub_icon.png")
        self.setWindowIcon(QIcon(icon_path))

        self.setWindowFlags(
            Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint
        )
        self.MAIN_function = main_function_ref
        self.setWindowTitle("FragHub 1.4.1")
        self.setGeometry(100, 100, 1280, 720)

        # --- NOUVEAU : QStackedWidget pour alterner les vues ---
        self.stacked_widget = QStackedWidget()

        # 1. Vue de configuration (Index 0)
        self.config_view = self._create_config_view()
        self.stacked_widget.addWidget(self.config_view)

        # 2. Vue de progression (Index 1)
        self.progress_view = ProgressView()  # UTILISE ProgressView
        self.stacked_widget.addWidget(self.progress_view)

        # Connexions des signaux de la vue de progression
        self.progress_view.stop_requested_signal.connect(self.handle_stop_request)
        self.progress_view.finish_requested_signal.connect(lambda: self.clean_exit(force_quit_app=False))

        self.setCentralWidget(self.stacked_widget)
        self.show_config_view()  # Démarrer en mode configuration
        # --- FIN NOUVEAU ---

        self.running = False
        self.progress_window = None  # Rendu obsolète
        self.thread = None
        self.stop_thread_flag = False

        self.error_occurred_signal.connect(self.handle_execution_error)
        self.task_finished_signal.connect(self.handle_task_finished)

    def _create_config_view(self):
        """Crée et retourne le widget de la vue de configuration (onglets + bouton START)."""
        config_container = QWidget()
        main_layout = QVBoxLayout(config_container)

        banner = QLabel()
        icon_path = os.path.join(BASE_DIR, "GUI", "assets", "FragHub_icon.png")
        pixmap = QPixmap(icon_path)

        if not pixmap.isNull():
            pixmap_scaled = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            banner.setPixmap(pixmap_scaled)

        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(banner)

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

        self.output_tab.output_directory_changed.connect(self.projects_tab.output_directory_changed_signal)

        self.start_button = QPushButton("START")
        self.start_button.setFixedSize(140, 60)
        self.start_button.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.start_button.clicked.connect(self.open_progress_window)
        main_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        return config_container

    def show_config_view(self):
        """Affiche la vue de configuration et restaure l'état."""
        self.stacked_widget.setCurrentIndex(0)
        self.setEnabled(True)
        self.start_button.setEnabled(True)

    def show_progress_view(self):
        """Affiche la vue de progression."""
        self.stacked_widget.setCurrentIndex(1)
        self.setEnabled(True)

    def open_progress_window(self):
        # --- Check selections before starting ---
        input_files = parameters_dict.get("input_directory")
        output_dir = parameters_dict.get("output_directory")

        missing_selections = []
        if not input_files:
            missing_selections.append("at least one input file")
        if not output_dir:
            missing_selections.append("an output directory")

        if missing_selections:
            message = "Please select " + " and ".join(missing_selections) + " before starting."
            QMessageBox.warning(self, "Selection Required", message)
            return
        # --- END OF CHECK ---

        if not self.running:
            # Remplacer la logique de minimisation/fenêtre externe
            self.show_progress_view()
            self.start_execution()

    def handle_stop_request(self):
        if self.running:
            self.stop_thread_flag = True

    def start_execution(self):
        if self.running:
            return

        self.running = True
        self.stop_thread_flag = False

        # Utiliser self.progress_view
        if self.progress_view:
            self.progress_view.progress_bar_widget.update_total_items(total=100, completed=0)
            self.progress_view.progress_bar_widget.update_progress_bar(0)

        if self.thread and self.thread.is_alive():
            self.stop_thread_flag = True
            self.thread.join()
            self.thread = None

        callbacks = {
            # Utiliser self.progress_view
            'progress': self.progress_view.update_progress_signal.emit,
            'total_items': self.progress_view.update_total_signal.emit,
            'prefix': self.progress_view.update_prefix_signal.emit,
            'item_type': self.progress_view.update_item_type_signal.emit,
            'step': self.progress_view.update_step_signal.emit,
            'completion': self.progress_view.completion_callback.emit,
            'deletion': self.progress_view.deletion_callback.emit
        }
        signals = {'error': self.error_occurred_signal, 'finished': self.task_finished_signal}
        stop_flag_provider = lambda: self.stop_thread_flag

        self.thread = Thread(target=run_main_in_worker,
                             args=(self.MAIN_function, callbacks, signals, stop_flag_provider), daemon=True,
                             name="MainWorkerThread_FragHub")
        self.thread.start()

    def handle_task_finished(self):
        self.running = False
        self.thread = None
        # Si la tâche a été arrêtée, revenir immédiatement à la vue de configuration
        if self.stop_thread_flag:
            self.show_config_view()
        self.stop_thread_flag = False

    def handle_execution_error(self, traceback_str):
        show_error_message(parent=self, title="Execution Error", message=traceback_str,
                           on_close=lambda: self.clean_exit(force_quit_app=False))

    def clean_exit(self, force_quit_app=True):
        if self.running and self.thread and self.thread.is_alive():
            self.stop_thread_flag = True
            self.thread.join(timeout=3.0)

        # Retirer la logique de fermeture de fenêtre externe
        self.progress_window = None
        self.running = False
        if force_quit_app:
            QApplication.instance().quit()
        else:
            # Revenir à la vue de configuration
            self.show_config_view()

    def closeEvent(self, event):
        if self.running:
            reply = QMessageBox.question(self, 'Quit FragHub?',
                                         "A process is running. Are you sure you want to quit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.clean_exit(force_quit_app=True)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()