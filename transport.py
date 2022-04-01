import json
import logging
import socket
import uuid

import consts
import db
import encryption
import models

try:
    _sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _sck.settimeout(consts.SCK_TIMEOUT)
    _sck.connect(("1.1.1.1", 80))
    MY_IP = _sck.getsockname()[0]
    _sck.close()
except (socket.timeout, ConnectionRefusedError, OSError):
    logging.warning("Connectivity error! Some functions may not be available.")


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


class Transmitter:
    def transmit(self, target: models.Contact, body: str):
        encrypted_body = encryption.Encryptor(target.key).encrypt(
            bytes(body, encoding="utf-8")
        )

        return self.send_to_every_contact(self.init_msg_dict(encrypted_body, target))

    def retransmit(self, msg):
        return self.send_to_every_contact(self.update_chain(msg))

    def send_to_every_contact(self, msg: dict):
        my_contacts = db.DB.fetch_all_contacts()
        success = 0
        for contact in my_contacts:
            try:
                self.send(contact, msg)
                success += 1
            except (socket.timeout, ConnectionRefusedError):
                logging.info(f"Cannot reach {contact.name} on {contact.ip}")
        logging.info(f"Transmitted msg to {success} contacts")
        return success

    def send(self, contact: models.Contact, msg: dict):
        transport = Transport(Transport.create_socket(), contact).connect()
        transport.send(msg)

    def init_msg_dict(self, body: bytes, target: models.Contact):
        return {
            "id": uuid.uuid4().hex,
            "type": models.MessageType.MESSAGE.value,
            "from": MY_IP,
            "to": target.ip,
            "body": str(body, encoding="utf-8"),
            "chain": [MY_IP],
        }

    def update_chain(self, message_dict: dict):
        message_dict["chain"].append(MY_IP)
        return message_dict
