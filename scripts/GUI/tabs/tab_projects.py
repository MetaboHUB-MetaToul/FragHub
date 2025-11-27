import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem,
    QSizePolicy, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from scripts.GUI.utils.global_vars import parameters_dict


class QToggleSwitch(QWidget):
    """
    A large custom ON/OFF switch with 'YES'/'NO' labels.
    Interaction is controlled by an internal state, enabling/disabling user clicks.
    """
    # Signal emitted when the state changes.
    state_changed = pyqtSignal(bool)

    def __init__(self, parent=None, initial_state=False):
        super().__init__(parent)
        self.setFixedSize(100, 50)
        self._state = initial_state
        # Interaction is disabled by default until the output directory is validated.
        self._enabled = False
        # Cursor indicates interaction is forbidden by default.
        self.setCursor(Qt.CursorShape.ForbiddenCursor)

    def mousePressEvent(self, event):
        """Toggles the state only if the switch is enabled."""
        if self._enabled:
            self._state = not self._state
            self.update()
            self.state_changed.emit(self._state)

    def paintEvent(self, event):
        """Custom drawing of the switch (background, text, and handle)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        # Set colors for ON (green) and OFF (red) states.
        background_color = QColor("#00C853") if self._state else QColor("#f44336")
        painter.setBrush(QBrush(background_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # Draw the rounded background rectangle.
        painter.drawRoundedRect(rect, rect.height() // 2, rect.height() // 2)

        # Set up text style.
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        text_color = QColor("#FFFFFF")
        painter.setPen(text_color)

        # Calculate text position for 'YES' or 'NO'.
        text = "YES" if self._state else "NO"
        text_pos = rect.left() + 10 if self._state else rect.right() - 35
        # Draw the YES/NO text.
        painter.drawText(text_pos, int(rect.height() * 0.65), text)

        # Draw the white circular button/handle.
        button_color = QColor("#FFFFFF")
        # Calculate button position based on state (right for ON, left for OFF).
        button_x = rect.width() - rect.height() + 5 if self._state else 5
        painter.setBrush(QBrush(button_color))
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        # Draw the button ellipse.
        painter.drawEllipse(button_x, 5, rect.height() - 10, rect.height() - 10)

    def sizeHint(self):
        """Provides the recommended size for the switch."""
        return QSize(100, 50)

    def is_checked(self):
        """Returns the current state of the switch."""
        return self._state

    def set_checked(self, state):
        """Programmatically sets the state of the switch."""
        if self._state != state:
            self._state = state
            self.update()

    def set_enabled(self, enabled):
        """Enables or disables user interaction with the switch."""
        self._enabled = enabled
        # Change cursor to reflect interaction status.
        cursor_shape = Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ForbiddenCursor
        self.setCursor(cursor_shape)
        self.update()


class ProjectsTab(QWidget):
    """
    GUI tab dedicated to project management, primarily the 'Reset Project' feature.
    The reset option is only enabled if the selected output directory is a FragHub project.
    """
    # Signal to receive updates about the output directory path.
    output_directory_changed_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.toggle_switch = None
        self.color_state = True
        self.timer = None

        # Initialize the reset flag in the global dictionary if missing.
        parameters_dict.setdefault("reset_updates", 0.0)

        self.setup_ui()
        self.setLayout(self.main_layout)

    def setup_ui(self):
        """Creates and arranges the tab's widgets."""
        self.main_layout = QVBoxLayout()

        # Spacer to push content to the vertical center.
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- RESET PROJECT Label (Large and Red) ---
        reset_label = QLabel("RESET PROJECT ?")
        reset_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        reset_label.setStyleSheet("font-size: 32px; font-weight: bold; color: red;")
        self.main_layout.addWidget(reset_label)

        # --- Blinking Effect for the Label ---
        self.timer = QTimer(self)
        # Connect the timer to the color toggle function.
        self.timer.timeout.connect(lambda: self.toggle_label_color(reset_label))
        self.timer.start(500)

        # --- Toggle Switch ---
        # The switch starts in the 'NO' (False) state.
        self.toggle_switch = QToggleSwitch(initial_state=False)
        self.main_layout.addWidget(self.toggle_switch, alignment=Qt.AlignmentFlag.AlignCenter)

        # Connect the switch's signal to the handler and the directory monitor.
        self.toggle_switch.state_changed.connect(self.on_toggle_state_changed)
        self.output_directory_changed_signal.connect(self.check_output_directory)

        # Spacer after the controls.
        self.main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Info button in the bottom-right ---
        info_button_layout = QHBoxLayout()
        info_button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        info_button = QPushButton("🛈")
        info_button.setFixedSize(30, 30)
        info_button.setToolTip(
            "Resetting the project deletes splash keys and output files from the "
            "selected project, to start fresh."
        )
        info_button_layout.addWidget(info_button)
        self.main_layout.addLayout(info_button_layout)

    def toggle_label_color(self, label):
        """
        Alternates the label's color to create a blinking visual effect,
        emphasizing the importance of the action.
        """
        # Alternate between a bright red and a dark red.
        if self.color_state:
            label.setStyleSheet("font-size: 32px; font-weight: bold; color: #FF4040;")
        else:
            label.setStyleSheet("font-size: 32px; font-weight: bold; color: #8B0000;")
        self.color_state = not self.color_state

    def check_output_directory(self, directory):
        """
        Checks for the presence of the `.fraghub` file in the selected directory.
        The switch is enabled only if the directory is a recognized FragHub project.
        """
        if directory:
            # Check for the existence of the hidden project file.
            fraghub_file = os.path.join(directory, ".fraghub")
            is_project_directory = os.path.isfile(fraghub_file)

            if is_project_directory:
                self.toggle_switch.set_enabled(True)
            else:
                self.toggle_switch.set_enabled(False)
                # Force the state back to 'NO' (False) if it's not a project directory.
                self.toggle_switch.set_checked(False)
                self.on_toggle_state_changed(False) # Also update global dict

    def on_toggle_state_changed(self, state):
        """
        Handles state changes of the toggle switch.
        Updates the global dictionary (1.0 for YES, 0.0 for NO).
        """
        global parameters_dict
        parameters_dict["reset_updates"] = 1.0 if state else 0.0