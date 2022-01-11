import os
import random
import string

from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileMovedEvent
from watchdog.observers import Observer


class DividingSocket:
    def __init__(self, tcp_socket):
        self.socket = tcp_socket

    def send(self, message):
        # Send until all files are sent
        if not isinstance(message, bytes):
            message = message.encode()

        self.socket.sendall(message)
        self.socket.send(b"<<done>>")

    def recv(self):
        data = b""
        # Receive all files
        while not data.endswith(b"<<done>>"):
            recv = self.socket.recv(1)
            data += recv
        data = data[:-8]
        return data


class Endpoint:
    def __init__(self, socket: DividingSocket, directory: str):
        self.socket = socket
        self.directory = directory
        self.to_upload = set()

    # Upload a single file
    def __upload_file(self, file_path: str):
        rel_path = os.path.relpath(file_path, self.directory)
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                with open(file_path, "rb") as file:
                    self.socket.send(b"file:" + rel_path.encode() + b":" + file.read())
            elif os.path.isdir(file_path):
                self.socket.send(b"directory:" + rel_path.encode())
        else:
            self.socket.send(b"remove:" + rel_path.encode())

    # Upload a set of files
    def upload_files(self, files: set):
        for file in files:
            self.__upload_file(file)
        self.socket.send("DONE")

    # Upload all files in a folder
    def __upload_folder(self, subdirectory):
        for f in os.listdir(subdirectory):
            f_path = os.path.join(subdirectory, f)
            if os.path.isfile(f_path):
                self.__upload_file(f_path)
            elif os.path.isdir(f_path):
                self.__upload_folder(f_path)

    def upload_folder(self):
        self.__upload_folder(self.directory)
        self.socket.send("DONE")

    # Download a folder
    def download_folder(self):
        files = set()
        msg = self.socket.recv()
        while msg != b"DONE":
            what, *data = msg.split(b':', 1)
            # Download a file
            if what == b"file":
                data = data[0]
                data = data.split(b':', 1)
                path, content = data
                files.add(os.path.join(self.directory, path.decode()))
                path = os.path.join(self.directory, path.decode())
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(content)
            # Download a directory
            elif what == b"directory":
                path = data[0].decode()
                files.add(os.path.join(self.directory, path))
                os.makedirs(os.path.join(self.directory, path), exist_ok=True)
            # Remove a file or a directory
            elif what == b"remove":
                path = data[0].decode()
                path = os.path.join(self.directory, path)
                files.add(path)
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        for root, dirs, files1 in os.walk(path, topdown=False):
                            for name in files1:
                                os.remove(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(path)
            msg = self.socket.recv()
        return files


class ClientEndpoint(Endpoint):
    def __init__(self, socket: DividingSocket, directory: str):
        super().__init__(socket, directory)

        self.version = 0
        self.watch_directory()

    # Modification function
    def __on_modification(self, event: FileSystemEvent):
        if isinstance(event, FileMovedEvent):
            self.to_upload.add(event.src_path)
            self.to_upload.add(event.dest_path)
        else:
            self.to_upload.add(event.src_path)

    def watch_directory(self):
        event_handler = FileSystemEventHandler()
        event_handler.on_modified = event_handler.on_created = event_handler.on_deleted = event_handler.on_moved = self.__on_modification
        observer = Observer()
        observer.schedule(event_handler, self.directory, recursive=True)
        observer.start()

    def sync(self):
        if len(self.to_upload) != 0:
            self.version += 1
        self.socket.send(f"SYNC:{self.version}")
        self.upload_files(self.to_upload)
        self.download_folder()
        self.to_upload.clear()
        self.version = int(self.socket.recv())


class ServerEndpoint(Endpoint):
    def sync(self, versions, version):
        # Get version and send files accordingly
        if version == 0:
            self.upload_folder()
            self.socket.send('1')
            versions.append(set())
            return
        files_to_upload = set()
        for i in versions[version:]:
            files_to_upload.update(i)
        if version > len(versions):
            versions.append(self.download_folder())
        self.upload_files(files_to_upload)
        self.socket.send(str(len(versions)))


def generate_random_id(length=128):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
