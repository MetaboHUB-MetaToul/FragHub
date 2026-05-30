from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from scripts.backend_vars import parameters_dict


class QToggleSwitch(QWidget):
    """
    A custom ON/OFF switch widget with 'YES'/'NO' labels and a modern visual style.
    It emits a stateChanged(bool) signal when its state changes.
    """
    state_changed = pyqtSignal(bool)

    def __init__(self, parent=None, initial_state=True):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._state = initial_state
        # Use QCursor.PointingHandCursor for better user experience.
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """Toggles the state when the switch is clicked."""
        self._state = not self._state
        self.update()
        self.state_changed.emit(self._state)

    def paintEvent(self, event):
        """Custom drawing of the switch, including background, text, and handle."""
        painter = QPainter(self)
        # Enable antialiasing for smoother rendering.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Set colors for ON (green) and OFF (red) states.
        background_color = QColor("#00C853") if self._state else QColor("#f44336")
        painter.setBrush(QBrush(background_color))
        painter.setPen(Qt.PenStyle.NoPen)
        # Draw the rounded background rectangle.
        painter.drawRoundedRect(rect, rect.height() // 2, rect.height() // 2)

        # Set up text style.
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        text_color = QColor("#FFFFFF")

        # Calculate text position based on state ('YES' or 'NO').
        if self._state:
            text = "YES"
            text_pos = rect.left() + 5
        else:
            text = "NO"
            text_pos = rect.right() - 25

        painter.setPen(text_color)
        # Draw the YES/NO text.
        painter.drawText(text_pos, rect.height() // 2 + 5, text)

        # Draw the white circular button/handle.
        button_color = QColor("#FFFFFF")
        # Calculate button position based on state (right for ON, left for OFF).
        button_x = rect.width() - rect.height() + 2 if self._state else 2
        button_y = 2
        painter.setBrush(QBrush(button_color))
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        # Draw the button ellipse.
        painter.drawEllipse(button_x, button_y, rect.height() - 4, rect.height() - 4)

    def sizeHint(self):
        """Provides the recommended size for the switch."""
        return QSize(60, 30)

    def is_checked(self):
        """Returns the current state of the switch."""
        return self._state

    def set_checked(self, state):
        """Programmatically sets the state of the switch."""
        if self._state != state:
            self._state = state
            self.update()


class OutputSettingTab(QWidget):
    """
    GUI tab for configuring the desired output file formats (CSV, MSP, JSON).
    """
    def __init__(self):
        super().__init__()

        # Initialize default parameters in the global dictionary (1.0 for ON/True).
        parameters_dict.setdefault('csv', 1.0)
        parameters_dict.setdefault('msp', 1.0)
        parameters_dict.setdefault('json', 1.0)

        main_layout = QVBoxLayout()

        # Spacer to push content to the vertical center.
        main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # Layout for central elements (switches and labels).
        center_layout = QVBoxLayout()
        # Center the main content horizontally and vertically within its space.
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add toggle switch rows for each output format.
        center_layout.addLayout(self._create_row("CSV", "csv"))
        center_layout.addLayout(self._create_row("MSP", "msp"))
        center_layout.addLayout(self._create_row("JSON", "json"))

        main_layout.addLayout(center_layout)

        # Spacer to push content to the vertical center.
        main_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Info button in the bottom-right corner ---
        info_button_layout = QHBoxLayout()
        # Align the button to the right.
        info_button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        info_button = QPushButton("🛈")
        info_button.setFixedSize(30, 30)

        # Set a helpful tooltip.
        info_button.setToolTip(
            "This tab lets you choose the output formats to be written by FragHub "
            "at the end of processing."
        )

        info_button_layout.addWidget(info_button)
        main_layout.addLayout(info_button_layout)

        self.setLayout(main_layout)

    def _create_row(self, label_text, parameter_key):
        """
        Creates a horizontal layout containing a toggle switch and a label,
        aligned to the center.
        """
        row_layout = QHBoxLayout()
        row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Determine initial state from the global dictionary.
        initial_state = parameters_dict.get(parameter_key, 1.0) == 1.0
        # Create the toggle switch and connect its signal to the update handler.
        toggle = QToggleSwitch(initial_state=initial_state)
        toggle.state_changed.connect(
            lambda state: self.update_parameter(parameter_key, state)
        )

        # Create the label for the format name (CSV, MSP, JSON).
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 14px;")

        # Add the switch and the label to the row.
        row_layout.addWidget(toggle)
        row_layout.addWidget(label)

        return row_layout

    def update_parameter(self, key, state):
        """
        Updates the global dictionary with 1.0 (ON) or 0.0 (OFF) based on the switch state.
        """
        global parameters_dict
        # Store state as 1.0 (ON) or 0.0 (OFF).
        parameters_dict[key] = 1.0 if state else 0.0