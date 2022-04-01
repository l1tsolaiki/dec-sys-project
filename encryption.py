from cryptography.fernet import Fernet


def generate_key():
    return Fernet.generate_key()


class Encryptor:
    def __init__(self, secret):
        self.encryptor = Fernet(secret)

    def encrypt(self, message):
        return self.encryptor.encrypt(bytes(message, "utf-8")).decode("utf-8")

    def decrypt(self, message):
        return self.encryptor.decrypt(bytes(message, "utf-8")).decode("utf-8")
