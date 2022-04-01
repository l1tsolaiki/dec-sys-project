import json
import socket

import consts
import encryption
import models


class Transport:
    def __init__(self, sck, contact: models.Contact):
        self.sck = sck
        self.encryptor = encryption.Encryptor(contact.key)
        self.ip = contact.ip

    def send(self, message: dict):
        bytes_msg = Transport._dump_to_bytes(message)
        encrypted = self.encryptor.encrypt(bytes_msg)
        self.sck.sendall(encrypted)
        print(f'Sent {encrypted}!')

    def receive_all(self):
        data = b""
        while True:
            received = self.sck.recv(consts.SCK_BUFF_SIZE)
            if len(received) < 1:
                break
            data += received

        bytes_msg = self.encryptor.decrypt(data)
        return Transport._load_from_bytes(bytes_msg)

    def connect(self):
        self.sck.connect((self.ip, int(consts.DAEMON_PORT)))
        return self

    @staticmethod
    def _dump_to_bytes(message: dict) -> bytes:
        print('TYPE IN DUMP:', type(message))
        print(message)
        return bytes(json.dumps(message), encoding="utf-8")

    @staticmethod
    def _load_from_bytes(message: bytes) -> dict:
        print('TYPE IN DUMP:', type(message))
        print(message)
        return json.loads(str(message, encoding="utf-8"))

    @staticmethod
    def create_socket():
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.settimeout(consts.SCK_TIMEOUT)
        return sck
