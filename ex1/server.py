#!/usr/bin/python3
import socket
import sys

from advanced_socket import AdvancedSocket

if len(sys.argv) != 2:
    print("Please provide a port", file=sys.stderr)
    exit(0)

port = sys.argv[1]
if not(port.isnumeric() and 0 <= int(port) <= 65535):
    print("Invalid port")
    exit(1)
port = int(port)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind(('', port))
    server = AdvancedSocket(sock)

    while True:
        data, addr = server.receive()

        print(data)
