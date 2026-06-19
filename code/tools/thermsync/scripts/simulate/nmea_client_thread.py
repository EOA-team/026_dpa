import socket
import time
from datetime import datetime, timezone

HOST = "127.0.0.1"
PORT = 5017
INTERVAL = 10  # seconds between reads


def format_utc(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%d.%m.%Y %H:%M:%S.") + f"{dt.microsecond // 1000:03d}"


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

try:
    while True:
        time.sleep(INTERVAL)

        # Flush everything received since last read
        sock.setblocking(False)
        buf = b""
        while True:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buf += data
            except BlockingIOError:
                break
        sock.setblocking(True)

        if not buf:
            print("No data received")
            continue

        # Take the last complete timestamp
        lines = buf.strip().split(b"\n")
        nmea_t = float(lines[-1].strip())

        system_t = time.time()
        offset = (nmea_t - system_t) * 1000
        print(f"System: {format_utc(system_t)}  |  NMEA: {format_utc(nmea_t)}  |  Offset: {offset:+.2f} ms")
except KeyboardInterrupt:
    print("\nStopping")
finally:
    sock.close()