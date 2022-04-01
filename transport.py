import json
import socket

import consts
import encryption
import models


class Transport:
    def __init__(self, contact: models.Contact):
        self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.encryptor = encryption.Encryptor(contact.key)
        self.ip = contact.ip

    def send(self, message: dict):
        bytes_msg = self._dump_to_bytes(message)
        self.sck.connect((self.ip, consts.DAEMON_PORT))
        self.sck.sendall(bytes_msg)

    def _dump_to_bytes(self, message: dict):
        return bytes(json.dumps(message), encoding="utf-8")

    def _load_from_bytes(self, message: bytes):
        return json.loads(str(message, encoding="utf-8"))
