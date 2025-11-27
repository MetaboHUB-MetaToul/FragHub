import traceback


def run_main_in_worker(main_function, callbacks, signals, stop_flag_provider):
    """
    A wrapper to execute the core application logic (main_function) in a separate thread.
    This function is designed to be the target for a threading.Thread object.

    :param main_function: The main processing function to be executed.
    :type main_function: function
    :param callbacks: A dictionary of callback functions for progress updates to the GUI.
    :type callbacks: dict
    :param signals: A dictionary of PyQt signals to emit upon error or completion.
    :type signals: dict
    :param stop_flag_provider: A function (or lambda) that returns the current state of the stop flag (bool).
    :type stop_flag_provider: function
    """
    try:
        # --- Custom Exception Handling for User Interruption ---
        try:
            # Attempt to import the specific InterruptedError defined in the MAIN module.
            from scripts.MAIN import InterruptedError
        except ImportError:
            # Define a local class if the custom exception cannot be found, ensuring execution continues.
            class InterruptedError(Exception):
                pass

        # --- Execution of Main Processing Function ---
        # Call the core function, mapping all necessary communication functions.
        main_function(
            progress_callback=callbacks['progress'],
            total_items_callback=callbacks['total_items'],
            prefix_callback=callbacks['prefix'],
            item_type_callback=callbacks['item_type'],
            step_callback=callbacks['step'],
            completion_callback=callbacks['completion'],
            deletion_callback=callbacks['deletion'],
            stop_flag=stop_flag_provider
        )

    except InterruptedError:
        # This exception is raised by the main logic when the user requests a stop.
        # This is a normal, handled interruption and does not trigger an error message box.
        pass

    except Exception:
        # --- Unhandled Exception Catch ---
        # Capture any other unexpected exception during main function execution.
        full_traceback = traceback.format_exc()
        # Emit the error signal to the GUI thread for display in an error message box.
        signals['error'].emit(full_traceback)

    finally:
        # This block is executed regardless of success, unhandled error, or interruption.
        # Emit the finished signal to allow the GUI thread to perform necessary cleanup.
        signals['finished'].emit()