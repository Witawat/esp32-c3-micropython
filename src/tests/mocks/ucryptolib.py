"""Mock module: ucryptolib (MicroPython crypto)"""


class aes:
    def __init__(self, key, mode, IV=None):
        self.key = key
        self.mode = mode
        self.iv = IV

    def encrypt(self, data):
        return bytes(data)

    def decrypt(self, data):
        return bytes(data)


MODE_ECB = 1
MODE_CBC = 2
MODE_CTR = 6
