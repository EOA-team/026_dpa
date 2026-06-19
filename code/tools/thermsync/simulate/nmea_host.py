import socket
import time

HOST = "127.0.0.1"
PORT = 5017

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()
print(f"NMEA host listening on {HOST}:{PORT}")

client, addr = server.accept()
print(f"Client connected: {addr}")

try:
    while True:
        t = time.time()
        client.sendall(f"{t:.6f}\n".encode())
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nShutting down")
finally:
    client.close()
    server.close()