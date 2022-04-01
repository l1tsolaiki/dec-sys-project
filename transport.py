import json
import logging
import socket
import uuid

import consts
import db
import encryption
import models


class Transport:
    def __init__(self, sck: socket.socket, contact: models.Contact):
        self.sck = sck
        self.encryptor = encryption.Encryptor(contact.key)
        self.ip = contact.ip

    def send(self, message: dict):
        bytes_msg = Transport._dump_to_bytes(message)
        encrypted = self.encryptor.encrypt(bytes_msg)
        self.sck.sendall(encrypted)

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
        return bytes(json.dumps(message), encoding="utf-8")

    @staticmethod
    def _load_from_bytes(message: bytes) -> dict:
        return json.loads(str(message, encoding="utf-8"))

    @staticmethod
    def create_socket():
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.settimeout(consts.SCK_TIMEOUT)
        return sck

    def get_my_ip(self):
        return self.sck.getsockname()[0]


class Sender:
    def __init__(self, contact: models.Contact):
        self.contact = contact

    def transmit(self, body: str):
        encrypted_body = encryption.Encryptor(self.contact.key).encrypt(
            bytes(body, encoding="utf-8")
        )
        my_contacts = db.DB.fetch_all_contacts()

        success = 0
        for contact in my_contacts:
            try:
                self.send(contact, encrypted_body)
                success += 1
            except (socket.timeout, ConnectionRefusedError):
                logging.info(f"Cannot reach {contact.name} on {contact.ip}")
        logging.info(f"Transmitted msg to {success} contacts")

    def send(self, contact: models.Contact, body: bytes):
        transport = Transport(Transport.create_socket(), contact).connect()
        transport.send(self.prepare_dict(transport, body))

    def prepare_dict(self, transport: Transport, body: bytes):
        return {
            "id": uuid.uuid4().hex,
            "type": models.MessageType.MESSAGE.value,
            "from": transport.get_my_ip(),
            "to": self.contact.ip,
            "body": str(body, encoding="utf-8"),
            "chain": [transport.get_my_ip()],
        }

    def update_dict(self, message_dict):
        message_dict["chain"].append()
