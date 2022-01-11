#!/usr/bin/python3
import socket
import sys

from advanced_socket import AdvancedSocket

if len(sys.argv) != 4:
    print("Please provide 3 arguments", file=sys.stderr)
    exit(1)

ip, port, file = sys.argv[1:4]
ip_numbers = ip.split('.')
if len(ip_numbers) != 4:
    print("Ip should contain 4 parts")
    exit(1)
for i in ip_numbers:
    if not(i.isnumeric() and 0 <= int(i) <= 255):
        print("Invalid ip")
        exit(1)

if not(port.isnumeric() and 0 <= int(port) <= 65535):
    print("Invalid port")
    exit(1)
port = int(port)

try:
    with open(file) as f:
        text = f.read()
except IOError:
    print("Incorrect file directory")
    exit(1)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    client = AdvancedSocket(sock)

    client.send(text, (ip, port))
