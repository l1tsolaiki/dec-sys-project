from cryptography.fernet import Fernet


def generate_key():
    return Fernet.generate_key().decode("utf-8")


class Encryptor:
    def __init__(self, secret):
        self.encryptor = Fernet(secret)

    def encrypt(self, message: bytes) -> bytes:
        return self.encryptor.encrypt(message)

    def decrypt(self, message: bytes) -> bytes:
        return self.encryptor.decrypt(message)
