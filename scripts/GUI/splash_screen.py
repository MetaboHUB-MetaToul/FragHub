from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QApplication
)
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt6.QtCore import Qt, QTimer, QRectF


class InfiniteSpinnerWidget(QWidget):
    """
    A custom widget that displays an infinite spinning loading animation.
    It uses QPainter and QTimer for smooth rendering.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        # Connect timer timeout to angle update.
        self._timer.timeout.connect(self._update_angle)
        self._timer.setInterval(25)  # Update interval in milliseconds.
        self._spinner_color = QColor(Qt.GlobalColor.white)
        self._pen_width = 3.0
        self.setFixedSize(40, 40)

    def _update_angle(self):
        """Decrements the starting angle and triggers a redraw."""
        # Decrement angle by 10 degrees and wrap around at 360.
        self._angle = (self._angle - 10) % 360
        self.update()

    def paintEvent(self, event):
        """Draws the spinning arc segment."""
        painter = QPainter(self)
        # Enable antialiasing for a smoother arc.
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate the bounding rectangle, accounting for pen width.
        padding = self._pen_width / 2.0
        rect = QRectF(
            padding, padding,
            float(self.width()) - self._pen_width,
            float(self.height()) - self._pen_width
        )

        if rect.width() <= 0 or rect.height() <= 0:
            return

        # Set pen properties for the arc.
        pen = QPen(self._spinner_color, self._pen_width, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Draw an arc segment of 90 degrees (90 * 16ths of a degree).
        # The starting angle is continually updated by the timer.
        painter.drawArc(rect, self._angle * 16, 90 * 16)

    def start_animation(self):
        """Starts the QTimer if it is not already running."""
        if not self._timer.isActive():
            self._timer.start()

    def stop_animation(self):
        """Stops the QTimer."""
        if self._timer.isActive():
            self._timer.stop()

    def set_color(self, color: QColor):
        """Sets the color of the spinner."""
        self._spinner_color = color
        self.update()

    def hideEvent(self, event):
        """Automatically stops the animation when the widget is hidden."""
        self.stop_animation()
        super().hideEvent(event)

    def showEvent(self, event):
        """Automatically starts the animation when the widget is shown."""
        self.start_animation()
        super().showEvent(event)


class LoadingSplashScreen(QWidget):
    """
    A frameless, transparent splash screen displayed during application startup,
    featuring an icon, a custom spinner, and a loading message.
    """
    def __init__(self, icon_pixmap: QPixmap, parent=None):
        super().__init__(parent)

        # Set window flags for a splash screen effect.
        self.setWindowFlags(
            Qt.WindowType.SplashScreen |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setup_ui(icon_pixmap)
        self.adjustSize()
        self._center_on_screen()

    def _setup_ui(self, icon_pixmap):
        """Initializes and arranges the widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Icon Label
        self.icon_label = QLabel()
        if not icon_pixmap.isNull():
            self.icon_label.setPixmap(icon_pixmap)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        # Spacer
        layout.addSpacerItem(
            QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # 2. Spinner Widget (centered)
        self.spinner = InfiniteSpinnerWidget(self)
        # Use QHBoxLayout for horizontal centering.
        spinner_layout = QHBoxLayout()
        spinner_layout.addStretch()
        spinner_layout.addWidget(self.spinner)
        spinner_layout.addStretch()
        layout.addLayout(spinner_layout)

        # Spacer
        layout.addSpacerItem(
            QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        )

        # 3. Message Label
        self.message_label = QLabel("Loading FragHub, please wait...")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Initial style for the message.
        self.message_label.setStyleSheet("QLabel { color : white; font-weight: bold; }")
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def _center_on_screen(self):
        """Moves the splash screen to the center of the primary screen."""
        if QApplication.primaryScreen():
            center_point = QApplication.primaryScreen().availableGeometry().center()
            self.move(
                center_point.x() - self.width() // 2,
                center_point.y() - self.height() // 2
            )

    def show_message(self, message, font_size=28, alignment=Qt.AlignmentFlag.AlignCenter, color=Qt.GlobalColor.white):
        """Updates the text message displayed on the splash screen."""
        self.message_label.setText(message)
        self.message_label.setAlignment(alignment)
        # Apply the new style (color is hardcoded to white in the original, maintaining that).
        self.message_label.setStyleSheet(
            f"QLabel {{ color: white; font-weight: bold; font-size: {font_size}px; }}"
        )

    def closeEvent(self, event):
        """Ensures the spinner animation is stopped when the splash screen is closed."""
        self.spinner.stop_animation()
        super().closeEvent(event)