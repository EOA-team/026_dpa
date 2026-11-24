"""Background listener for the quit key on stdin (safe over Remote Desktop)."""

import threading


class QuitListener:
    """Background thread watching for the quit key on stdin (RDP-safe)."""

    def __init__(self, quit_key: str = "q") -> None:
        self._quit_key = quit_key.lower()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="QuitListener"
        )

    @property
    def quit_requested(self) -> bool:
        return self._stop_event.is_set()

    def start(self) -> None:
        self._thread.start()
        print(f"[KEY] Type <{self._quit_key.upper()}> + Enter to stop.")

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                key = input()
            except EOFError:
                return
            if key.strip().lower() == self._quit_key:
                print("[KEY] Quit requested.")
                self._stop_event.set()
