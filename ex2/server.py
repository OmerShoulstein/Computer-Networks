#!/usr/bin/python3
import os
import socket
import sys

from utils import DividingSocket, generate_random_id, ServerEndpoint

PORT = int(sys.argv[1])

versions = {}


def handle_client(client: DividingSocket):
    client_id = client.recv().decode()

    client_folder = os.path.join('folders', client_id)
    server_endpoint = ServerEndpoint(client, client_folder)
    # New Client
    if client_id == '0':
        client_id = generate_random_id()
        print(client_id)
        os.makedirs((os.path.join('folders', client_id)), exist_ok=True)
        client.send(client_id)
        server_endpoint.directory = os.path.join('folders', client_id)
        versions[client_id] = []
        server_endpoint.download_folder()
    else:
        # Get version and send files accordingly
        version = int(client.recv().decode().split(':')[1])
        try:
            server_endpoint.sync(versions[client_id], version)
        except KeyError:
            client.send('bad Key')
            return

    msg = client.recv().decode()
    # Sync until client disconects
    while msg != "bye":
        command = msg.split(':')
        if command[0] == "SYNC":
            server_endpoint.sync(versions[client_id], int(command[1]))
        msg = client.recv().decode()


def main():
    with socket.create_server(('', PORT)) as server:
        while True:
            client, address = server.accept()
            with client:
                client = DividingSocket(client)
                handle_client(client)


if __name__ == '__main__':
    main()
