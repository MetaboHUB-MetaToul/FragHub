from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpacerItem,
    QSizePolicy, QPushButton
)
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import pyqtSignal, Qt

# Import the global parameters dictionary for state management.
from scripts.GUI.utils.global_vars import parameters_dict


class QToggleSwitch(QWidget):
    """
    A custom ON/OFF switch widget implemented with QWidget and QPainter.
    It emits a stateChanged(bool) signal when its state changes.
    """
    state_changed = pyqtSignal(bool)

    def __init__(self, parent=None, initial_state=False):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._state = initial_state
        # Use QCursor.PointingHandCursor for better UX.
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        """Toggles the state when the switch is clicked."""
        self._state = not self._state
        self.update()
        self.state_changed.emit(self._state)

    def paintEvent(self, event):
        """Custom drawing of the switch (background, text, and button)."""
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
        painter.setPen(text_color)

        # Calculate text position based on state.
        if self._state:
            text = "ON"
            text_pos = rect.left() + 12
        else:
            text = "OFF"
            text_pos = rect.right() - 32

        # Draw the ON/OFF text.
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

    def is_checked(self):
        """Returns the current state of the switch."""
        return self._state

    def set_checked(self, state):
        """Programmatically sets the state of the switch."""
        if self._state != state:
            self._state = state
            self.update()


class DeNovoTab(QWidget):
    """
    GUI tab dedicated to configuring de novo calculation options.
    It manages controls for activation and parameter adjustment (e.g., PPM tolerance).
    """

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.toggle_de_novo = None
        self.ppm_field = None

        self.initialize_parameters()
        self.create_de_novo_options()
        self.setLayout(self.layout)

    def initialize_parameters(self):
        """Initializes the default 'de novo' related values in the global parameters dictionary."""
        global parameters_dict
        # 1.0 for ON, 0.0 for OFF (for compatibility with expected float type).
        parameters_dict.setdefault("calculate_de_novo", 0.0)
        parameters_dict.setdefault("de_novo_ppm_tolerance", 10.0)

    def create_de_novo_options(self):
        """Creates and arranges all widgets within the de novo tab."""

        # Spacer to vertically center the main controls.
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Row 1: De Novo Calculation Activation Control ---
        de_novo_layout = QHBoxLayout()
        de_novo_layout.addStretch()  # Center alignment

        # Initialize the toggle switch based on the current global parameter value.
        initial_state = parameters_dict.get("calculate_de_novo", 0.0) == 1.0
        self.toggle_de_novo = QToggleSwitch(initial_state=initial_state)
        # Connect the switch to its update handler.
        self.toggle_de_novo.state_changed.connect(self.on_toggle_changed)
        de_novo_layout.addWidget(self.toggle_de_novo)

        # Label for the calculation feature.
        label = QLabel("Calculate fragment formula")
        label.setFont(QFont("Arial", 12))
        de_novo_layout.addWidget(label)

        # Add a critical warning about compatibility issues.
        warning_label = QLabel(
            "(warning not compatible with most reprocessing software)"
        )
        warning_font = QFont("Arial", 9)
        warning_font.setItalic(True)
        warning_label.setFont(warning_font)
        warning_label.setStyleSheet("color: red;")
        de_novo_layout.addWidget(warning_label)

        de_novo_layout.addStretch()
        self.layout.addLayout(de_novo_layout)

        # --- Row 2: PPM Tolerance Parameter Input ---
        ppm_layout = QHBoxLayout()
        ppm_layout.addStretch()  # Center alignment

        # Label for the PPM tolerance input field.
        ppm_label = QLabel("ppm tolerance:")
        ppm_label.setFont(QFont("Arial", 10))
        ppm_layout.addWidget(ppm_label)

        # Initialize input field with the current global PPM value.
        initial_ppm = str(parameters_dict.get("de_novo_ppm_tolerance", 10.0))
        self.ppm_field = QLineEdit(initial_ppm)
        self.ppm_field.setFixedWidth(60)
        # Connect the text change to its update handler.
        self.ppm_field.textChanged.connect(
            lambda value: self.handle_text_change("de_novo_ppm_tolerance", value)
        )
        ppm_layout.addWidget(self.ppm_field)

        ppm_layout.addStretch()
        self.layout.addLayout(ppm_layout)

        # Spacer to push the info button to the bottom.
        self.layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # --- Info button in the bottom right corner ---
        info_button_layout = QHBoxLayout()
        info_button_layout.addStretch()

        info_button = QPushButton("🛈")
        info_button.setFixedSize(30, 30)
        # Detailed tooltip explanation for the user.
        info_button.setToolTip(
            "Enables the de novo chemical formula calculation for each spectrum.\n"
            "The PPM tolerance is used for the precision of the formula matching.\n"
            "Warning, this option makes the output databases incompatible with most reprocessing software."
        )
        info_button_layout.addWidget(info_button)
        self.layout.addLayout(info_button_layout)

    def on_toggle_changed(self, state):
        """Updates the global dictionary when the 'calculate_de_novo' switch is toggled."""
        global parameters_dict
        # Store state as 1.0 (ON) or 0.0 (OFF).
        parameters_dict["calculate_de_novo"] = 1.0 if state else 0.0

    def handle_text_change(self, key, value):
        """Updates the global dictionary when a text field (e.g., PPM tolerance) is changed."""
        global parameters_dict
        try:
            # Attempt to convert the text value to a float.
            parameters_dict[key] = float(value)
        except ValueError:
            # Ignore non-numeric input to prevent crashes.
            pass