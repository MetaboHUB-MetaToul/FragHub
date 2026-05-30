from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpacerItem,
    QSizePolicy, QPushButton
)
from PyQt6.QtGui import QFont, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import QSize, pyqtSignal, Qt

# Import the global parameters dictionary for state management.
from scripts.backend_vars import parameters_dict


class QToggleSwitch(QWidget):
    """
    A custom ON/OFF switch widget implemented with QWidget and QPainter.
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
        """Custom drawing of the switch (background, text, and handle)."""
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

        # Calculate text position based on state.
        if self._state:
            text = "ON"
            text_pos = rect.left() + 5
        else:
            text = "OFF"
            text_pos = rect.right() - 25

        painter.setPen(text_color)
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


class FiltersTab(QWidget):
    """
    GUI tab dedicated to configuring various data processing filters.
    It manages activation switches and parameter input fields for each filter.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.create_filters_ui()
        self.setLayout(self.layout)

    def get_filter_list(self):
        """Returns a list of all defined filter names."""
        return [
            "normalize_intensity",
            "remove_peak_above_precursormz",
            "check_minimum_peak_requiered",
            "reduce_peak_list",
            "remove_spectrum_under_entropy_score",
            "keep_mz_in_range",
            "check_minimum_of_high_peaks_requiered",
        ]

    def create_filters_ui(self):
        """Initializes parameters and builds the UI layout for all filters."""
        global parameters_dict
        filters = self.get_filter_list()

        # Initialize each filter to 1.0 (ON) by default in `parameters_dict` if missing.
        for filter_name in filters:
            parameters_dict.setdefault(filter_name, 1.0)

        self.add_filters_to_layout(self.layout)

    def add_filters_to_layout(self, layout):
        """Dynamically creates and adds the widgets for each filter to the layout."""
        filters = self.get_filter_list()

        # Dictionary of filter messages for tooltips.
        filter_messages = {
            "normalize_intensity": (
                "This function normalizes the intensity of all peaks in a given "
                "spectrum to the maximum intensity."
            ),
            "remove_peak_above_precursormz": (
                "This function removes all peaks from the spectrum whose m/z value "
                "is greater than the precursor's m/z value + 5 Da."
            ),
            "check_minimum_peak_requiered": (
                "This function checks whether a given mass spectrum contains a "
                "minimum number of peaks. If the spectrum contains fewer peaks "
                "than the minimum requirement, it deletes the spectrum."
            ),
            "reduce_peak_list": (
                "This function reduces the peak list to a specified maximum number "
                "of peaks. Peaks are retained based on their intensity, prioritizing "
                "peaks with greater intensity."
            ),
            "remove_spectrum_under_entropy_score": (
                "The entropy score of the spectrum is calculated during processing. "
                "If a spectrum has an entropy score lower than the minimum required, "
                "it is deleted."
            ),
            "keep_mz_in_range": (
                "This function deletes all spectra whose precursor m/z is not "
                "between the specified `min` and `max` values."
            ),
            "check_minimum_of_high_peaks_requiered": (
                "This function checks whether a given peak list has a required minimum "
                "number of high peaks. A high peak is defined as a peak whose intensity "
                "is above a certain percentage (intensity_percent) of the maximum intensity. "
                "If the condition is not met, the spectrum is deleted."
            ),
        }

        # Main vertical layout container for filter rows.
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)

        for filter_name in filters:
            # Horizontal layout for each filter row.
            filter_layout = QHBoxLayout()
            filter_layout.setSpacing(5)

            # 1. ToggleSwitch (ON/OFF)
            initial_state = parameters_dict.get(filter_name, 1.0) == 1.0
            toggle = QToggleSwitch(initial_state=initial_state)
            # Connect the state change signal to the update function.
            toggle.state_changed.connect(
                lambda state, name=filter_name: self.toggle_filter(state, name)
            )
            filter_layout.addWidget(toggle)

            # 2. Filter name label.
            label = QLabel(filter_name)
            label.setFont(QFont("Arial", 12))
            label.setFixedHeight(30)
            filter_layout.addWidget(label)

            # 3. Info button (🛈) with detailed tooltip.
            info_button = QPushButton("🛈")
            info_button.setFixedSize(25, 25)
            info_button.setToolTip(
                filter_messages.get(filter_name, "No message defined for this filter.")
            )
            filter_layout.addWidget(info_button)

            # Add an expandable space to push controls to the right.
            filter_layout.addStretch()

            # 4. Add specific parameter fields for the filter, if required.
            self.add_additional_fields(filter_layout, filter_name)

            main_layout.addLayout(filter_layout)

        # Apply the main layout.
        layout.addLayout(main_layout)

    def add_additional_fields(self, filter_layout, filter_name):
        """Adds specific QLineEdit fields for filters that require parameters."""
        global parameters_dict

        if filter_name == "check_minimum_peak_requiered":
            n_peaks_layout = QHBoxLayout()
            n_peaks_label = QLabel("N peaks:")
            n_peaks_label.setFont(QFont("Arial", 10))
            n_peaks_label.setFixedWidth(50)
            n_peaks_layout.addWidget(n_peaks_label)

            parameter_key = "check_minimum_peak_requiered_n_peaks"
            # Initialize parameter value and field.
            parameters_dict.setdefault(parameter_key, 3.0)
            text_field = QLineEdit(str(parameters_dict[parameter_key]))
            text_field.setFixedWidth(60)
            n_peaks_layout.addWidget(text_field)
            # Connect handler for text changes.
            text_field.textChanged.connect(
                lambda value, key=parameter_key: self.handle_text_change(key, value)
            )
            filter_layout.addLayout(n_peaks_layout)

        elif filter_name == "reduce_peak_list":
            max_peaks_layout = QHBoxLayout()
            max_peaks_label = QLabel("Max peaks:")
            max_peaks_label.setFont(QFont("Arial", 10))
            max_peaks_label.setFixedWidth(70)
            max_peaks_layout.addWidget(max_peaks_label)

            parameter_key = "reduce_peak_list_max_peaks"
            parameters_dict.setdefault(parameter_key, 500.0)
            text_field = QLineEdit(str(parameters_dict[parameter_key]))
            text_field.setFixedWidth(60)
            max_peaks_layout.addWidget(text_field)

            text_field.textChanged.connect(
                lambda value, key=parameter_key: self.handle_text_change(key, value)
            )
            filter_layout.addLayout(max_peaks_layout)

        elif filter_name == "keep_mz_in_range":
            mz_range_layout = QHBoxLayout()

            # 'From' field
            from_key = "keep_mz_in_range_from_mz"
            parameters_dict.setdefault(from_key, 50.0)
            from_label = QLabel("From:")
            from_label.setFont(QFont("Arial", 10))
            from_label.setFixedWidth(40)
            mz_range_layout.addWidget(from_label)

            from_field = QLineEdit(str(parameters_dict[from_key]))
            from_field.setFixedWidth(60)
            mz_range_layout.addWidget(from_field)
            from_field.textChanged.connect(
                lambda value, key=from_key: self.handle_text_change(key, value)
            )

            # Separator spacer
            spacer = QSpacerItem(
                20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
            )
            mz_range_layout.addSpacerItem(spacer)

            # 'To' field
            to_key = "keep_mz_in_range_to_mz"
            parameters_dict.setdefault(to_key, 2000.0)
            to_label = QLabel("To:")
            to_label.setFont(QFont("Arial", 10))
            to_label.setFixedWidth(40)
            mz_range_layout.addWidget(to_label)

            to_field = QLineEdit(str(parameters_dict[to_key]))
            to_field.setFixedWidth(60)
            mz_range_layout.addWidget(to_field)
            to_field.textChanged.connect(
                lambda value, key=to_key: self.handle_text_change(key, value)
            )

            filter_layout.addLayout(mz_range_layout)

        elif filter_name == "check_minimum_of_high_peaks_requiered":
            high_peaks_layout = QHBoxLayout()

            # Intensity percentage field
            intensity_key = "check_minimum_of_high_peaks_requiered_intensity_percent"
            parameters_dict.setdefault(intensity_key, 5.0)
            intensity_label = QLabel("Intensity %:")
            intensity_label.setFont(QFont("Arial", 10))
            intensity_label.setFixedWidth(80)
            high_peaks_layout.addWidget(intensity_label)

            intensity_field = QLineEdit(str(parameters_dict[intensity_key]))
            intensity_field.setFixedWidth(60)
            high_peaks_layout.addWidget(intensity_field)
            intensity_field.textChanged.connect(
                lambda value, key=intensity_key: self.handle_text_change(key, value)
            )

            # Minimum number of high peaks field
            n_peaks_key = "check_minimum_of_high_peaks_requiered_no_peaks"
            parameters_dict.setdefault(n_peaks_key, 2.0)
            n_peaks_label = QLabel("N peaks:")
            n_peaks_label.setFont(QFont("Arial", 10))
            n_peaks_label.setFixedWidth(70)
            high_peaks_layout.addWidget(n_peaks_label)

            n_peaks_field = QLineEdit(str(parameters_dict[n_peaks_key]))
            n_peaks_field.setFixedWidth(60)
            high_peaks_layout.addWidget(n_peaks_field)
            n_peaks_field.textChanged.connect(
                lambda value, key=n_peaks_key: self.handle_text_change(key, value)
            )

            filter_layout.addLayout(high_peaks_layout)

        elif filter_name == "remove_spectrum_under_entropy_score":
            entropy_layout = QHBoxLayout()

            score_key = "remove_spectrum_under_entropy_score_value"
            parameters_dict.setdefault(score_key, 0.5)
            score_label = QLabel("Score:")
            score_label.setFont(QFont("Arial", 10))
            score_label.setFixedWidth(50)
            entropy_layout.addWidget(score_label)

            score_field = QLineEdit(str(parameters_dict[score_key]))
            score_field.setFixedWidth(60)
            entropy_layout.addWidget(score_field)
            score_field.textChanged.connect(
                lambda value, key=score_key: self.handle_text_change(key, value)
            )

            filter_layout.addLayout(entropy_layout)

    def toggle_filter(self, state, filter_name):
        """Updates the global dictionary when a filter's toggle switch is changed."""
        global parameters_dict
        # Store state as 1.0 (ON) or 0.0 (OFF).
        parameters_dict[filter_name] = 1.0 if state else 0.0

    def handle_text_change(self, key, value):
        """Updates the global dictionary when a parameter text field is changed."""
        global parameters_dict
        try:
            # Attempt to convert the text value to a float.
            parameters_dict[key] = float(value)
        except ValueError:
            # Ignore non-numeric input to prevent crashes.
            pass