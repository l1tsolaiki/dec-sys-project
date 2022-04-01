import enum


class Contact:

    def __init__(self, name, ip, key=None):
        self.name = name
        self.ip = ip
        self.key = key


# class MessageType(enum.StrEnum):
#     KEY = 'KEY'
#     MESSAGE = 'MESSAGE'


# class Message:
#
#     def __init__(self, type):