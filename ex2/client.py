#!/usr/bin/python3
import socket
import sys
import time

from utils import DividingSocket, ClientEndpoint

if len(sys.argv) == 6:
    _, IP, PORT, PATH, INTERVAL, ID = sys.argv
else:
    _, IP, PORT, PATH, INTERVAL = sys.argv
    ID = '0'

PORT = int(PORT)
INTERVAL = float(INTERVAL)


def main():
    client_endpoint = ClientEndpoint(None, PATH)

    with socket.create_connection((IP, PORT)) as client:
        client = DividingSocket(client)
        client_endpoint.socket = client

        global ID
        client.send(ID)
        if ID == '0':
            ID = client.recv().decode()
            client_endpoint.upload_folder()
        else:
            client.send('SYNC:' + str(client_endpoint.version))
            client_endpoint.download_folder()

        client.send("bye")

    while True:
        with socket.create_connection((IP, PORT)) as client:
            client = DividingSocket(client)
            client_endpoint.socket = client

            client.send(ID)
            client_endpoint.sync()
            client.send("bye")

        time.sleep(INTERVAL)


if __name__ == '__main__':
    main()
