import socket
import time

HOST = "127.0.0.1"
PORT = 5017

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))
print(f"Connected to {HOST}:{PORT}")

try:
    while True:
        data = sock.recv(4096)
        if not data:
            break
        print(data.decode().strip())
except KeyboardInterrupt:
    print("\nStopping")
finally:
    sock.close()