import socket

HOST = "192.168.168.100"
PORT = 5017

def parse_zda(parts):
    """$GPZDA,HHMMSS.sss,DD,MM,YYYY,tzh,tzm"""
    time_str = parts[1]
    if len(time_str) < 6:
        return None
    hh, mm, ss = time_str[0:2], time_str[2:4], time_str[4:]
    dd, mo, yyyy = parts[2], parts[3], parts[4]
    return f"{yyyy}-{mo}-{dd} {hh}:{mm}:{ss} UTC"

print(f"Connecting to APX at {HOST}:{PORT}...")

sock = None
try:
    sock = socket.create_connection((HOST, PORT), timeout=5)
    sock.settimeout(10)
    print("Connected! Receiving ZDA\n")

    buffer = ""
    while True:
        data = sock.recv(1024)
        if not data:
            print("⚠️  Connection closed by APX")
            break
        buffer += data.decode("ascii", errors="ignore")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if line.startswith("$GPZDA") or line.startswith("$GNZDA"):
                parts = line.split(",")
                if len(parts) >= 5 and parts[1] and parts[2]:
                    timestamp = parse_zda(parts)
                    if timestamp:
                        print(f"[ZDA] {timestamp}")

except ConnectionRefusedError:
    print("❌ Connection refused")
except socket.timeout:
    print("❌ Timeout — APX stopped sending")
except OSError as e:
    print(f"❌ Network error: {e}")
except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
        print("🔌 Connection closed cleanly.")