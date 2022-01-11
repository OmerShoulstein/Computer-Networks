#!/usr/bin/python3
import socket


class AdvancedSocket:
    PACKAGE_SIZE = 100
    TIMEOUT = 2

    def __init__(self, sock: socket.socket):
        self.sock = sock

    def send_one_package(self, package: bytes, address: tuple) -> None:
        while True:
            # Setting timeout (waiting for ack)
            self.sock.settimeout(self.TIMEOUT)
            self.sock.sendto(package, address)  # Sending the packet
            try:
                data, addr = self.sock.recvfrom(self.PACKAGE_SIZE)  # Receiving
            except socket.timeout:  # Ack didn't arrive in 2 seconds
                continue  # Sending again.
            if data == package:  # Got the correct ack.
                break

    def send(self, data: str, address: tuple) -> None:
        msg = data.encode()
        for i in range(0, len(msg), self.PACKAGE_SIZE - 2):
            # Adding the packet ID.
            header = (i // (self.PACKAGE_SIZE - 2)
                      ).to_bytes(2, byteorder="little")
            self.send_one_package(
                header + msg[i:i + self.PACKAGE_SIZE - 2], address)

    def receive(self) -> None:
        last_seq = -1
        while True:
            data, address = self.sock.recvfrom(self.PACKAGE_SIZE)
            seq_num = int.from_bytes(data[0:2], "little")  # Packet ID
            # If this is the packet that we've been waiting for.
            if seq_num == last_seq + 1:
                # Printing the data.
                print(data[2:].decode(), end="", flush=True)
                last_seq = seq_num
            self.sock.sendto(data, address)  # Sending ack.
