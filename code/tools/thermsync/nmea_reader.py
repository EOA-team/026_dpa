"""Threaded reader for the Applanix APX NMEA stream.

Connects to the APX over TCP and continuously reads the stream, keeping the
latest $--ZDA UTC time in a cache. A receive timeout detects dead connections
and the reader reconnects automatically until it is stopped.
"""

import socket
import threading
from datetime import datetime, timezone

APX_HOST = "192.168.168.100"
APX_PORT = 5017

CONNECT_TIMEOUT_S = 5.0  # max wait for the TCP connection to the APX
RECV_TIMEOUT_S = 2.0  # silence longer than this means the connection is dead

_JOIN_TIMEOUT_S = 5.0
_RECV_SIZE = 4096

_ZDA = "ZDA"
_ZDA_REQUIRED_FIELDS = 5  # talker(e.g. $ZDA), time, day, month, year 
_TIME_REQUIRED_CHARS = 6  # hhmmss - whole seconds at minimum


def parse_zda(sentence: str) -> datetime | None:
    """Parse a $--ZDA sentence into a timezone-aware UTC datetime.

    Example: "$GPZDA,160012.71,11,06,2026,00,00*7B"
             -> 2026-06-11 16:00:12.710000 UTC
    Returns None for incomplete or malformed sentences.
    """
    try:
        sentence = sentence.strip()
        if not sentence.startswith("$") or sentence[3:6] != _ZDA:
            return None
        body = sentence.split("*", 1)[0]
        parts = body.split(",")
        if len(parts) < _ZDA_REQUIRED_FIELDS:
            return None
        time_str, day, month, year = parts[1], parts[2], parts[3], parts[4]
        if not time_str or not day or not month or not year:
            return None
        if len(time_str) < _TIME_REQUIRED_CHARS:
            return None
        hours = int(time_str[0:2])
        minutes = int(time_str[2:4])
        seconds = float(time_str[4:])
        return datetime(
            int(year),
            int(month),
            int(day),
            hours,
            minutes,
            int(seconds),
            round((seconds % 1) * 1_000_000),
            tzinfo=timezone.utc,
        )
    except (ValueError, IndexError):
        return None


class NmeaReader:
    """Background reader caching the latest $--ZDA UTC time."""

    def __init__(self, host: str = APX_HOST, port: int = APX_PORT) -> None:
        self._host = host
        self._port = port
        self._gps_time: datetime | None = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="NmeaReader"
        )

    def start(self) -> None:
        print(f"[NMEA] Connecting to {self._host}:{self._port} ...")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=_JOIN_TIMEOUT_S)
        print("[NMEA] Stopped.")

    def get(self) -> datetime | None:
        """Return the latest received ZDA time, or None if none arrived yet."""
        with self._lock:
            return self._gps_time

    def _run(self) -> None:
        buffer = ""
        try:
            with socket.create_connection(
                (self._host, self._port), timeout=CONNECT_TIMEOUT_S
            ) as sock:
                sock.settimeout(RECV_TIMEOUT_S)
                print("[NMEA] Connected.")
                while not self._stop_event.is_set():
                    data = sock.recv(_RECV_SIZE)
                    if not data:
                        break  # the APX closed the connection
                    buffer += data.decode("ascii", errors="ignore")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        parsed = parse_zda(line)
                        if parsed is not None:
                            with self._lock:
                                self._gps_time = parsed
        except (socket.timeout, OSError) as exc:
            print(f"[NMEA] Connection lost: {exc}")
        print("[NMEA] Disconnected.")
