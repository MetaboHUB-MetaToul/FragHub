from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QWidget, QSizePolicy,
    QPushButton, QSplitter, QTabWidget, QScrollArea
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
import sys
import time
import ctypes
import os
import platform


# Determine the base directory for resource files, handling PyInstaller executable or script execution.
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    # Base directory when running as a Python script.
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Set the application model ID for better integration on Windows.
if platform.system() == "Windows":
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FragHub")


def format_time(time_in_seconds):
    """Converts a time in seconds into HH:MM:SS format."""
    hours, remainder = divmod(time_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"


class ProgressBarWidget(QWidget):
    """
    A custom widget displaying a progress bar, a prefix message, and detailed
    progress information (percentage, item count, and estimated time).
    """
    # Signal emitted when progress reaches 100%. Passes prefix and suffix strings.
    progress_completed_signal = pyqtSignal(str, str)

    def __init__(self, update_progress_signal, update_total_signal, update_prefix_signal, update_item_type_signal,
                 parent=None):
        super().__init__(parent)
        self.total_items = 100
        self.start_time = time.time()
        self.item_type = "items"

        self._setup_ui()
        self._connect_signals(update_progress_signal, update_total_signal,
                              update_prefix_signal, update_item_type_signal)

    def _setup_ui(self):
        """Initializes and arranges the sub-widgets within the horizontal layout."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Prefix label (e.g., "Processing file...")
        self.progress_prefix = QLabel("Starting...")
        self.progress_prefix.setFont(QFont("Arial", 12))
        self.progress_prefix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.progress_prefix)

        # QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Apply custom styling to the progress bar.
        self.progress_bar.setStyleSheet("""
            QProgressBar { height: 24px; border: 1px solid #000; border-radius: 4px; background: #e0e0e0; }
            QProgressBar::chunk { background-color: #3b8dff; border-radius: 4px; }
        """)
        layout.addWidget(self.progress_bar)

        # Suffix label (e.g., "50.00% | 50/100 items [00:01:30 < 00:01:30, 0.50 items/s]")
        self.progress_suffix = QLabel("0.00%")
        self.progress_suffix.setFont(QFont("Arial", 12))
        self.progress_suffix.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.progress_suffix.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.progress_suffix)

        self.setLayout(layout)

    def _connect_signals(self, update_progress_signal, update_total_signal,
                         update_prefix_signal, update_item_type_signal):
        """Connects external signals from the main worker to the update methods."""
        update_progress_signal.connect(self.update_progress_bar)
        update_total_signal.connect(self.update_total_items)
        update_prefix_signal.connect(self.update_progress_prefix)
        update_item_type_signal.connect(self.update_item_type)

    def update_item_type(self, item_type):
        """Sets the name of the items being processed (e.g., 'files', 'spectra')."""
        self.item_type = item_type

    def update_progress_prefix(self, prefix_text):
        """Updates the descriptive text before the progress bar."""
        self.progress_prefix.setText(prefix_text)

    def update_progress_bar(self, progress):
        """Updates the progress value and recalculates the detailed suffix text."""
        self.progress_bar.setValue(progress)

        progress_percent = (progress / self.total_items) * 100 if self.total_items > 0 else 0
        elapsed_time = time.time() - self.start_time
        items_per_second = progress / elapsed_time if elapsed_time > 0 else 0
        remaining_items = self.total_items - progress
        estimated_time_left = remaining_items / items_per_second if items_per_second > 0 else 0

        # Construct the detailed suffix string with time and rate.
        self.progress_suffix.setText(
            f"{progress_percent:.2f}% | {progress}/{self.total_items} {self.item_type} "
            f"[{format_time(elapsed_time)} < {format_time(estimated_time_left)}, {items_per_second:.2f} {self.item_type}/s]"
        )

        # Emit signal upon completion.
        if progress >= self.total_items:
            self.progress_completed_signal.emit(self.progress_prefix.text(), self.progress_suffix.text())

    def update_total_items(self, total, completed=0):
        """Sets the maximum value of the progress bar and resets the timer."""
        self.total_items = total
        self.progress_bar.setMaximum(total)
        self.start_time = time.time()
        self.update_progress_bar(completed)


class ProgressView(QWidget):
    """
    A dedicated view for monitoring the application's execution progress.
    It includes a progress bar and a report area for completed steps.
    """
    # Signals for worker communication:
    update_progress_signal = pyqtSignal(int)
    update_total_signal = pyqtSignal(int, int)
    update_prefix_signal = pyqtSignal(str)
    update_item_type_signal = pyqtSignal(str)
    update_step_signal = pyqtSignal(str)
    completion_callback = pyqtSignal(str)
    deletion_callback = pyqtSignal(str)
    # Signals for button interaction:
    stop_requested_signal = pyqtSignal()
    finish_requested_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress_bar_widget = None
        self.report_content = QVBoxLayout()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Initializes all widgets and sets up the main layout."""
        # --- Banner ---
        banner = QLabel()
        icon_path = os.path.join(BASE_DIR, "GUI", "assets", "FragHub_icon.png")
        # Scale down the icon for the progress view.
        pixmap = QPixmap(icon_path).scaled(
            150, 150, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        banner.setPixmap(pixmap)
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Splitter for Report/Progress areas ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top half: Report Area (Scrollable)
        self.top_tab_widget = QTabWidget()
        self.report_tab = QWidget()
        self.report_layout = QVBoxLayout()

        # Widget to hold the dynamically added report items.
        self.report_widget = QWidget()
        self.report_widget.setLayout(self.report_content)
        # Stretch item to keep content pushed to the top.
        self.report_content.addStretch()
        self.report_widget.setMinimumWidth(1)

        # Scroll area for the report content.
        self.report_scroll = QScrollArea()
        self.report_scroll.setWidgetResizable(True)
        self.report_scroll.setWidget(self.report_widget)

        self.report_layout.addWidget(self.report_scroll)
        self.report_tab.setLayout(self.report_layout)
        self.top_tab_widget.addTab(self.report_tab, "Report")
        splitter.addWidget(self.top_tab_widget)

        # Bottom half: Progress Bar Area
        self.bottom_tab_widget = QTabWidget()
        self.progress_tab = QWidget()
        self.progress_layout = QVBoxLayout()

        # Create and add the ProgressBarWidget.
        self.progress_bar_widget = self._create_progress_bar_widget()
        self.progress_layout.addWidget(self.progress_bar_widget)

        self.progress_tab.setLayout(self.progress_layout)
        self.bottom_tab_widget.addTab(self.progress_tab, "Progress")
        splitter.addWidget(self.bottom_tab_widget)

        # Set minimum height for progress area and configure stretch factors.
        self.bottom_tab_widget.setMinimumHeight(60)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 0)

        # --- Main Layout ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(banner)
        main_layout.addWidget(splitter)

        # --- Finish Button ---
        self.finish_button = QPushButton("FINISH")
        self.finish_button.setFixedSize(120, 40)
        self.finish_button.setStyleSheet(
            "background-color: green; color: white; font-weight: bold; font-size: 14px; padding: 10px; border-radius: 5px;"
        )
        self.finish_button.clicked.connect(self.finish_requested_signal.emit)
        self.finish_button.hide()

        # --- Stop Button ---
        self.stop_button = QPushButton("STOP")
        self.stop_button.setFixedSize(120, 40)
        self.stop_button.setStyleSheet(
            "background-color: red; color: white; font-weight: bold; font-size: 14px; padding: 10px; border-radius: 5px;"
        )
        self.stop_button.clicked.connect(self.stop_button_clicked)

        # --- Button Layout (centered) ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.finish_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def _create_progress_bar_widget(self):
        """Utility method to create and connect the ProgressBarWidget instance."""
        pb_widget = ProgressBarWidget(
            self.update_progress_signal, self.update_total_signal,
            self.update_prefix_signal, self.update_item_type_signal
        )
        # Connect the internal completion signal to the report handler.
        pb_widget.progress_completed_signal.connect(self.add_to_report)
        return pb_widget

    def _connect_signals(self):
        """Connects signals for adding information to the Report tab."""
        self.update_step_signal.connect(self.add_step_to_report)
        self.completion_callback.connect(self.handle_completion)
        self.deletion_callback.connect(self.add_deletion_to_report)

    def stop_button_clicked(self):
        """Emits the stop request signal and updates the stop button appearance."""
        self.stop_requested_signal.emit()
        self.stop_button.setEnabled(False)
        self.stop_button.setText("STOPPING...")

    def handle_completion(self, completion_message):
        """Replaces the progress bar with a completion message and updates buttons."""
        # Clean the progress area.
        while self.progress_layout.count() > 0:
            if item := self.progress_layout.takeAt(0):
                if widget := item.widget():
                    widget.deleteLater()

        # Add the final completion message.
        message_label = QLabel(completion_message)
        message_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_layout.addWidget(message_label)

        # Update buttons for post-completion state.
        self.stop_button.hide()
        self.finish_button.show()

    def add_to_report(self, prefix_text, suffix_text):
        """Adds a completed process (e.g., a processed file) to the Report tab."""
        report_layout = QHBoxLayout()
        report_layout.setContentsMargins(10, 5, 10, 5)
        report_layout.setSpacing(10)

        # Prefix Label (e.g., "File processing:").
        prefix_label = QLabel(prefix_text)
        prefix_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        prefix_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        report_layout.addWidget(prefix_label)

        # Simulated completed progress bar (purely visual for the report).
        fake_progress_bar = QProgressBar()
        fake_progress_bar.setMinimum(0)
        fake_progress_bar.setMaximum(100)
        fake_progress_bar.setValue(100)
        fake_progress_bar.setTextVisible(False)
        fake_progress_bar.setStyleSheet(
            """QProgressBar { height: 18px; border: 1px solid #000; border-radius: 4px; background: #e0e0e0; } QProgressBar::chunk { background-color: #3b8dff; border-radius: 4px; }"""
        )
        report_layout.addWidget(fake_progress_bar)

        # Suffix Label (detailed time/rate stats).
        suffix_label = QLabel(suffix_text)
        suffix_label.setFont(QFont("Arial", 10))
        suffix_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        report_layout.addWidget(suffix_label)

        # Add the new report widget to the report content layout.
        report_widget = QWidget()
        report_widget.setLayout(report_layout)
        # Insert before the stretch item to maintain content-at-top alignment.
        self.report_content.insertWidget(self.report_content.count() - 1, report_widget)

        # Scroll to the bottom of the report.
        self.report_scroll.verticalScrollBar().setValue(
            self.report_scroll.verticalScrollBar().maximum()
        )

    def add_step_to_report(self, step_message):
        """Adds a major processing step message (e.g., 'Starting Filtering') to the Report tab."""
        new_step = QLabel(step_message)
        new_step.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        new_step.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Insert before the stretch item.
        self.report_content.insertWidget(self.report_content.count() - 1, new_step)

        # Scroll to the bottom.
        self.report_scroll.verticalScrollBar().setValue(
            self.report_scroll.verticalScrollBar().maximum()
        )

    def add_deletion_to_report(self, deletion_message):
        """Adds a message about spectrum deletion to the Report tab, colored red."""
        new_deletion = QLabel(deletion_message)
        new_deletion.setFont(QFont("Arial", 12, QFont.Weight.Normal))
        new_deletion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_deletion.setStyleSheet("color: red;")
        # Insert before the stretch item.
        self.report_content.insertWidget(self.report_content.count() - 1, new_deletion)

        # Scroll to the bottom.
        self.report_scroll.verticalScrollBar().setValue(
            self.report_scroll.verticalScrollBar().maximum()
        )

    def reset_view(self):
        """Resets the view's state for a new execution run."""

        # 1. Clean the progress area (remove completion message if present).
        while self.progress_layout.count() > 0:
            if item := self.progress_layout.takeAt(0):
                if widget := item.widget():
                    widget.deleteLater()

        # 2. Recreate and re-add the ProgressBarWidget.
        self.progress_bar_widget = self._create_progress_bar_widget()
        self.progress_layout.addWidget(self.progress_bar_widget)

        # 3. Reset buttons to the initial 'STOP' state.
        self.stop_button.show()
        self.stop_button.setEnabled(True)
        self.stop_button.setText("STOP")
        self.finish_button.hide()

        # 4. Clear the Report tab content (keep only the stretch item).
        widgets_to_remove = []
        # Iterate and remove all items except the last one (which is the QSpacerItem).
        for i in range(self.report_content.count() - 1):
            item = self.report_content.itemAt(0)
            if item.widget():
                widgets_to_remove.append(item.widget())
            self.report_content.removeItem(item)

        for widget in widgets_to_remove:
            widget.deleteLater()