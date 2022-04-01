import json
import logging
import socket
import uuid

import consts
import db
import encryption
import models


class Transport:
    def __init__(self, sck: socket.socket, peer: models.Peer):
        self.sck = sck
        self.encryptor = encryption.Encryptor(peer.key)
        self.ip = peer.ip

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
    def transmit(self, target: models.Peer, msg: dict):
        init = self.default_msg_dict(target)
        init.update(msg)
        msg = init

        if msg.get('body'):
            msg['body'] = encryption.Encryptor(target.key).encrypt(
                msg['body'].encode('utf-8')
            ).decode('utf-8')

        return self.send_to_every_peer(msg)

    def retransmit(self, msg):
        return self.send_to_every_peer(self.update_chain(msg))

    def send_to_every_peer(self, msg: dict):
        my_peers = db.DB.fetch_all_peers()
        success = 0
        for peer in my_peers:
            try:
                self.send(peer, msg)
                success += 1
            except (socket.timeout, ConnectionRefusedError):
                logging.info(f"Cannot reach {peer.name} on {peer.ip}")
        return success

    def send(self, peer: models.Peer, msg: dict):
        transport = Transport(Transport.create_socket(), peer).connect()
        transport.send(msg)

    def default_msg_dict(self, target: models.Peer):
        my_peer_id = db.get_peer_id()
        return {
            "id": uuid.uuid4().hex,
            "from": my_peer_id,
            "to": target.peer_id,
            "chain": [my_peer_id],
        }

    def update_chain(self, message_dict: dict):
        my_peer_id = db.get_peer_id()
        message_dict["chain"].append(my_peer_id)
        return message_dict
