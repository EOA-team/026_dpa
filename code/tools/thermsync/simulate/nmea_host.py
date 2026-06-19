import socket
import time

HOST = "127.0.0.1"
PORT = 5017
MSG_SIZE = 1400  # bytes per tick (~1 TCP segment)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
print(f"NMEA host listening on {HOST}:{PORT} (MSG_SIZE={MSG_SIZE} B)")

client, addr = server.accept()
print(f"Client connected: {addr}")

try:
    while True:
        t = time.time()
        # Two lines per tick: dummy padding + real timestamp
        msg = b"x" * MSG_SIZE + b"\n" + f"{t:.6f}\n".encode()
        client.sendall(msg)
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nShutting down")
finally:
    client.close()
    server.close()