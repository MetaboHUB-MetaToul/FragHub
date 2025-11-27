import sys
import traceback
from PyQt6.QtWidgets import QMessageBox, QTextEdit, QApplication
from PyQt6.QtCore import QCoreApplication


def show_error_message(parent, title, message, on_close=None):
    """
    Displays an error in an enlarged QMessageBox with a QTextEdit area
    to show detailed traceback information.

    :param parent: The parent widget (or None).
    :param title: The title of the error window.
    :param message: The detailed error message (e.g., traceback).
    :param on_close: A callback function to execute when the dialog is closed with 'Ok'.
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText("An error occurred during execution.")
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

    # Text area for displaying the detailed message (traceback).
    text_area = QTextEdit()
    text_area.setText(message)
    text_area.setReadOnly(True)
    # Use a monospace font for clean traceback viewing.
    text_area.setStyleSheet("font-family: Consolas, monospace; font-size: 10pt;")
    text_area.setMinimumSize(700, 350)

    try:
        # Attempt to add the QTextEdit to the QMessageBox's layout for an integrated view.
        grid_layout = msg_box.layout()
        # Add the widget below the existing content, spanning all columns.
        grid_layout.addWidget(text_area, grid_layout.rowCount(), 0, 1, grid_layout.columnCount())
        msg_box.setMinimumSize(750, 450)
    except Exception as layout_e:
        # Fallback if the layout manipulation fails (e.g., in some environments).
        sys.stderr.write(
            f"Warning: Could not add QTextEdit to QMessageBox layout ({layout_e}). "
            f"Using setDetailedText as fallback."
        )
        msg_box.setDetailedText(message)

    clicked_button = msg_box.exec()

    # Execute the optional callback function if the user closed the box with 'Ok'.
    if clicked_button == QMessageBox.StandardButton.Ok and on_close:
        try:
            on_close()
        except Exception:
            sys.stderr.write(
                "ERROR: Exception in the on_close callback of show_error_message.\n"
            )
            traceback.print_exc()


def exception_hook(exctype, value, tb):
    """
    Global exception hook to capture and display unhandled Python exceptions
    via a PyQt QMessageBox before application exit.

    :param exctype: The type of the exception.
    :param value: The exception instance.
    :param tb: The traceback object.
    """
    # Format the full traceback string.
    error_message = ''.join(traceback.format_exception(exctype, value, tb))
    sys.stderr.write(f"Uncaught exception:\n{error_message}")

    # Check if a QApplication instance exists before attempting to show the GUI.
    if QCoreApplication.instance():
        # Display the error using the GUI utility function.
        show_error_message(
            parent=None,
            title="Unhandled Exception",
            message=error_message
        )
    # Ensure the application terminates after an unhandled exception.
    sys.exit(1)