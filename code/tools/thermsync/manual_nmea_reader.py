"""
Reads NMEA-0183 sentences from a TCP stream (e.g. Applanix APX).

Supported sentences
-------------------
  PASHR    – proprietary roll / pitch / heading      (100 Hz)
  ZDA      – UTC date + time                         (100 Hz)
  GGA      – position, altitude, fix quality         (100 Hz)
  PTNL,AVR – yaw / tilt / roll, moving baseline RTK  (100 Hz)


TODO: Do not understand how buffer fills up, but it works xD
TODO: Do not fully understand how data are retrieved from buffer, but it works xD
"""
import time
import socket
from dataclasses import dataclass
from typing import TypeVar, Type

APX_HOST = "192.168.168.100"
APX_PORT = 5017

_RECV_SIZE = 65536  # bytes to read per drain() call


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PASHR:
    """Proprietary roll / pitch / heading sentence (Trimble/Applanix).
    https://help.fieldsystems.trimble.com/sps/nmea0183-messages-pashr.htm
    """
    heading:       float   # degrees, true north
    roll:          float   # degrees, + = right
    pitch:         float   # degrees, + = bow up
    roll_acc:      float   # degrees (accuracy estimate)
    pitch_acc:     float   # degrees (accuracy estimate)
    heading_acc:   float   # degrees (accuracy estimate)
    gnss_quality:  int     # 0-6
    imu_alignment: int     # 0-4


@dataclass
class ZDA:
    """UTC date and time sentence.
    https://gpsd.gitlab.io/gpsd/NMEA.html#_zda_time_date
    """
    time_utc: str   # hhmmss.ss
    day:      int
    month:    int
    year:     int
    ltzh:     int   # local timezone hours offset  (-13 … 13)
    ltzn:     int   # local timezone minutes offset (0, 15, 30, 45)


@dataclass
class GGA:
    """Time, position and fix related data.
    https://help.fieldsystems.trimble.com/sps/nmea0183-messages-gga.htm
    """
    time_utc:    str            # hhmmss.ss
    latitude:    float | None   # decimal degrees, + = North
    longitude:   float | None   # decimal degrees, + = East
    quality:     int            # 0-6
    num_svs:     int            # number of satellites in use
    hdop:        float | None
    altitude_m:  float | None   # orthometric height (MSL), metres
    geoid_sep_m: float | None   # geoid separation, metres
    dgps_age:    float | None   # age of differential data, seconds
    station_id:  str            # reference station ID (may be empty)


@dataclass
class PTNLAVR:
    """Time, yaw, tilt/roll, range for moving baseline RTK.
    https://help.fieldsystems.trimble.com/sps/nmea0183-messages-ptnl_avr.htm

    NOTE: tilt and roll are mutually exclusive per variant:
      variant 1: ...,tilt,Tilt,,,range,...   (tilt present, roll empty)
      variant 2: ...,,,,roll,Roll,range,...  (tilt empty, roll present)
    """
    time_utc: str            # hhmmss.ss
    yaw:      float | None   # degrees
    tilt:     float | None   # degrees (or None if roll variant)
    roll:     float | None   # degrees (or None if tilt variant)
    range_m:  float | None   # baseline length between antennas, metres
    quality:  int            # 0-4
    pdop:     float | None
    num_svs:  int            # number of satellites in solution


T = TypeVar("T", PASHR, ZDA, GGA, PTNLAVR)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nmea_lat(value: str, hemi: str) -> float | None:
    """Convert ddmm.mmmmm + N/S to signed decimal degrees."""
    if not value:
        return None
    deg = int(float(value) / 100)
    minutes = float(value) - deg * 100
    dec = deg + minutes / 60.0
    return -dec if hemi.upper() == "S" else dec


def _nmea_lon(value: str, hemi: str) -> float | None:
    """Convert dddmm.mmmmm + E/W to signed decimal degrees."""
    if not value:
        return None
    deg = int(float(value) / 100)
    minutes = float(value) - deg * 100
    dec = deg + minutes / 60.0
    return -dec if hemi.upper() == "W" else dec


def _float_or_none(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _int_or_zero(s: str) -> int:
    try:
        return int(s)
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Parsers  (module-level, pure functions)
# ---------------------------------------------------------------------------

def _parse_zda(sentence: str) -> ZDA | None:
    try:
        body = sentence[:sentence.index("*")] if "*" in sentence else sentence
        p = body.split(",")
        if len(p) < 5:
            return None
        return ZDA(
            time_utc = p[1],
            day      = int(p[2]),
            month    = int(p[3]),
            year     = int(p[4]),
            ltzh     = int(p[5]) if len(p) > 5 and p[5] else 0,
            ltzn     = int(p[6]) if len(p) > 6 and p[6] else 0,
        )
    except (ValueError, IndexError):
        return None


def _parse_pashr(sentence: str) -> PASHR | None:
    try:
        body = sentence[:sentence.index("*")] if "*" in sentence else sentence
        p = body.split(",")
        if len(p) < 12:
            return None
        return PASHR(
            heading       = float(p[2]),
            roll          = float(p[4]),
            pitch         = float(p[5]),
            roll_acc      = float(p[7]),
            pitch_acc     = float(p[8]),
            heading_acc   = float(p[9]),
            gnss_quality  = int(p[10]),
            imu_alignment = int(p[11]),
        )
    except (ValueError, IndexError):
        return None


def _parse_gga(sentence: str) -> GGA | None:
    try:
        body = sentence[:sentence.index("*")] if "*" in sentence else sentence
        p = body.split(",")
        if len(p) < 15:
            return None
        return GGA(
            time_utc    = p[1],
            latitude    = _nmea_lat(p[2], p[3]),
            longitude   = _nmea_lon(p[4], p[5]),
            quality     = _int_or_zero(p[6]),
            num_svs     = _int_or_zero(p[7]),
            hdop        = _float_or_none(p[8]),
            altitude_m  = _float_or_none(p[9]),   # p[10] == "M"
            geoid_sep_m = _float_or_none(p[11]),  # p[12] == "M"
            dgps_age    = _float_or_none(p[13]),
            station_id  = p[14] if len(p) > 14 else "",
        )
    except (ValueError, IndexError):
        return None


def _parse_ptnl_avr(sentence: str) -> PTNLAVR | None:
    try:
        body = sentence[:sentence.index("*")] if "*" in sentence else sentence
        p = body.split(",")
        # p[0]="$PTNL"  p[1]="AVR"   p[2]=time   p[3]=yaw    p[4]="Yaw"
        # p[5]=tilt      p[6]="Tilt"  p[7]=roll   p[8]="Roll" p[9]=range
        # p[10]=quality  p[11]=pdop   p[12]=svs
        if len(p) < 13 or p[1].strip().upper() != "AVR":
            return None
        return PTNLAVR(
            time_utc = p[2],
            yaw      = _float_or_none(p[3]),
            tilt     = _float_or_none(p[5]),
            roll     = _float_or_none(p[7]),
            range_m  = _float_or_none(p[9]),
            quality  = _int_or_zero(p[10]),
            pdop     = _float_or_none(p[11]),
            num_svs  = _int_or_zero(p[12]),
        )
    except (ValueError, IndexError):
        return None


# ---------------------------------------------------------------------------
# Routing tables  (add new sentence types here only)
# ---------------------------------------------------------------------------

# Maps sentence token → parser function
_PARSERS: dict[str, callable] = {
    "PASHR": _parse_pashr,
    "GPZDA": _parse_zda,
    "GNZDA": _parse_zda,
    "GLZDA": _parse_zda,
    "GAZDA": _parse_zda,
    "GPGGA": _parse_gga,
    "GNGGA": _parse_gga,
    "GLGGA": _parse_gga,
    "GAGGA": _parse_gga,
    "PTNL":  _parse_ptnl_avr,  # subtype "AVR" checked inside parser
}

# Maps sentence token → dataclass type (used as cache key)
_TYPE_MAP: dict[str, type] = {
    "PASHR": PASHR,
    "GPZDA": ZDA,
    "GNZDA": ZDA,
    "GLZDA": ZDA,
    "GAZDA": ZDA,
    "GPGGA": GGA,
    "GNGGA": GGA,
    "GLGGA": GGA,
    "GAGGA": GGA,
    "PTNL":  PTNLAVR,
}


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------

class NmeaReader:

    def __init__(self, host: str = APX_HOST, port: int = APX_PORT):
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._buf  = bytearray()
        # Maps dataclass type → latest successfully parsed instance
        self._latest: dict[type, object] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> None:
        self._sock = socket.create_connection((self._host, self._port))
        self._sock.setblocking(False)
        print(f"[NMEA] connected to {self._host}:{self._port}")

    def disconnect(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None
        print("[NMEA] disconnected")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def drain(self) -> int:
        """
        Pull all available bytes from the socket and parse every complete
        sentence found in the buffer. Non-blocking: returns immediately
        if no new data is available.

        Returns the number of new sentences parsed.
        """
        self._latest.clear()
        self._recv()
        return self._parse_buffer()

    def get_latest(self, sentence_type: Type[T]) -> T | None:
        """
        Return the most recently parsed sentence of *sentence_type*, or
        None if none has been received yet.

        Example:
            zda   = reader.get_latest(ZDA)
            gga   = reader.get_latest(GGA)
            pashr = reader.get_latest(PASHR)
            avr   = reader.get_latest(PTNLAVR)
        """
        return self._latest.get(sentence_type)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _recv(self) -> None:
        """Drain the OS socket buffer into self._buf. Never blocks."""
        if self._sock is None:
            return
        try:
            while True:
                chunk = self._sock.recv(_RECV_SIZE)
                if not chunk:
                    break
                self._buf.extend(chunk)
        except BlockingIOError:
            pass  # no more data right now — normal for non-blocking socket

    def _parse_buffer(self) -> int:
        """
        Walk self._buf, extract every complete '$…\\n' sentence, iterate
        newest-first so the first hit per type is the latest in the buffer.
        Returns the number of unique types updated.
        """
        raw   = bytes(self._buf)
        lines = raw.split(b"\n")
        tail  = lines[-1]   # incomplete sentence — keep for next drain()

        updated = 0
        for line in reversed(lines[:-1]):
            line = line.rstrip(b"\r")
            if not line.startswith(b"$"):
                continue

            sentence  = line.decode("ascii", errors="ignore")
            token     = sentence[1:].split(",", 1)[0].upper()
            parser    = _PARSERS.get(token)
            dest_type = _TYPE_MAP.get(token)

            if parser is None:
                continue
            if dest_type in self._latest:
                continue   # already have a newer result for this type

            result = parser(sentence)
            if result is not None:
                self._latest[dest_type] = result
                updated += 1

        self._buf = bytearray(tail)
        return updated

    @staticmethod
    def get_timestamp(zda: ZDA) -> str:
        """Return 'YYMMDD_HHMMSS_ms' from a ZDA sentence."""
        yy = str(zda.year)[-2:]
        mm = f"{zda.month:02d}"
        dd = f"{zda.day:02d}"
        hh = zda.time_utc[0:2]
        mi = zda.time_utc[2:4]
        ss = zda.time_utc[4:6]
        ms = f"{round(float('0.' + zda.time_utc.split('.')[1]) * 1000):03d}"
        return f"{yy}{mm}{dd}_{hh}{mi}{ss}_{ms}"


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    reader = NmeaReader()
    reader.connect()

    for i in range(10):
        time.sleep(1)
        reader.drain()
        print(reader.get_latest(ZDA))
        print(reader.get_latest(PASHR))
        print(reader.get_latest(GGA))
        print(reader.get_latest(PTNLAVR))
        print(reader.get_timestamp(reader.get_latest(ZDA)))

    reader.disconnect()