"""
keypress_listener.py
--------------------
Background thread that listens for a specific keypress via stdin.
Works over Remote Desktop where msvcrt.kbhit() fails.

Usage:
    listener = KeypressListener(quit_key="q")
    listener.start()

    if listener.quit_requested:
        break

    listener.stop()
"""

import threading
import logging

logger = logging.getLogger(__name__)


class KeypressListener:

    def __init__(self, quit_key: str = "q"):
        self._quit_key = quit_key.lower()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="KeypressListener")

    def start(self):
        self._thread.start()
        print(f"[KEY] Type <{self._quit_key.upper()}> + Enter to stop.")

    def stop(self):
        self._stop_event.set()

    @property
    def quit_requested(self) -> bool:
        return self._stop_event.is_set()

    def _run(self):
        while not self._stop_event.is_set():
            try:
                key = input()
                if key.strip().lower() == self._quit_key:
                    logger.info(f"[KEY] '{self._quit_key.upper()}' pressed — quit requested.")
                    self._stop_event.set()
            except EOFError:
                break  # stdin closed