import enum


class Peer:
    def __init__(self, peer_id, name, ip=None, key=None):
        self.peer_id = peer_id
        self.name = name
        self.ip = ip
        self.key = key
        self.show = False

    def __str__(self):
        template = 'Name: {}\nIP: {}\nKey: {}'
        return template.format(self.name, self.ip, self.key)

    def to_tuple(self):
        if self.show:
            self.show = False
            return self.name, self.ip, self.key
        return self.peer_id, self.name, self.ip, '***'

    def show_key(self):
        self.show = True
        return self


class MessageType(enum.Enum):
    MESSAGE = 'MESSAGE'
    ACK = 'ACK'
