"""
nmea_reader.py
--------------
Background thread that connects to the Applanix APX NMEA TCP stream and
caches the latest $GPZDA / $GNZDA timestamp.

Usage:
    reader = NmeaReader()
    reader.start()
    gps_time, lag_ms = reader.get()
    reader.stop()
"""

import socket
import threading
import time
from datetime import datetime, timezone

APX_HOST          = "192.168.168.100"
APX_PORT          = 5017
CONNECT_TIMEOUT_S = 5
RECV_TIMEOUT_S    = 2
RECONNECT_DELAY_S = 2


class NmeaReader:

    def __init__(self, host: str = APX_HOST, port: int = APX_PORT):
        self._host        = host
        self._port        = port
        self._lock        = threading.Lock()
        self._gps_time    = None   # latest parsed datetime
        self._received_at = None   # monotonic time of last update
        self._stop_event  = threading.Event()
        self._thread      = threading.Thread(target=self._run, daemon=True, name="NmeaReader")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self):
        self._thread.start()
        print(f"[NMEA] Connecting to {self._host}:{self._port} ...")

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=5)
        print("[NMEA] Stopped.")

    def get(self) -> tuple[datetime | None, float | None]:
        """
        Returns (gps_time, lag_ms).
        lag_ms = how many ms ago the timestamp was received.
        Returns (None, None) if no timestamp received yet.
        """
        with self._lock:
            if self._gps_time is None:
                return None, None
            lag_ms = (time.monotonic() - self._received_at) * 1000.0
            return self._gps_time, lag_ms

    @property
    def is_alive(self) -> bool:
        return self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _update(self, gps_time: datetime):
        with self._lock:
            self._gps_time    = gps_time
            self._received_at = time.monotonic()

    def _run(self):
        while not self._stop_event.is_set():
            sock = None
            try:
                sock = socket.create_connection((self._host, self._port), timeout=CONNECT_TIMEOUT_S)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # disable Nagle batching
                sock.settimeout(RECV_TIMEOUT_S)
                print("[NMEA] Connected.")

                buffer = ""
                while not self._stop_event.is_set():
                    try:
                        data = sock.recv(4096)
                    except socket.timeout:
                        print("[NMEA] ⚠ No data — reconnecting ...")
                        break
                    if not data:
                        print("[NMEA] ⚠ Connection closed — reconnecting ...")
                        break

                    buffer += data.decode("ascii", errors="ignore")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line.startswith("$GPZDA") or line.startswith("$GNZDA"):
                            ts = self._parse_zda(line)
                            if ts:
                                self._update(ts)

            except ConnectionRefusedError:
                print(f"[NMEA] ❌ Connection refused — retrying in {RECONNECT_DELAY_S}s ...")
            except OSError as e:
                print(f"[NMEA] ❌ Network error: {e} — retrying in {RECONNECT_DELAY_S}s ...")
            finally:
                if sock:
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    sock.close()

            if not self._stop_event.is_set():
                time.sleep(RECONNECT_DELAY_S)

        print("[NMEA] Thread exiting.")

    @staticmethod
    def _parse_zda(sentence: str) -> datetime | None:
        try:
            if "*" in sentence:
                sentence = sentence[:sentence.index("*")]
            parts = sentence.split(",")
            if len(parts) < 5:
                return None
            time_str, dd, mo, yyyy = parts[1], parts[2], parts[3], parts[4]
            if not all([time_str, dd, mo, yyyy]) or len(time_str) < 6:
                return None
            hh       = int(time_str[0:2])
            mm       = int(time_str[2:4])
            ss_full  = float(time_str[4:])
            ss       = int(ss_full)
            microsec = round((ss_full - ss) * 1_000_000)
            return datetime(int(yyyy), int(mo), int(dd), hh, mm, ss, microsec, tzinfo=timezone.utc)
        except (ValueError, IndexError):
            return None

if __name__ == "__main__":
    reader = NmeaReader()
    reader.start()

    try:
        while True:
            gps_time, lag_ms = reader.get()
            if gps_time is not None:
                print(f"[ZDA] {gps_time}  lag={lag_ms:.1f}ms")
            time.sleep(1.1)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        reader.stop()
