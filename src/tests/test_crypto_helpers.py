"""
Unit tests: crypto helpers (hash / HMAC / hex / base64 / PBKDF2)
ใช้ known test vectors มาตรฐาน
"""

import unittest

import _env  # noqa: F401

from crypto.crypto_helpers import HashHelper, SSLHelper


class TestHashHelper(unittest.TestCase):

    def test_sha256_known(self):
        d = HashHelper.sha256(b"abc")
        self.assertEqual(
            HashHelper.to_hex(d),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_sha256_empty(self):
        self.assertEqual(
            HashHelper.to_hex(HashHelper.sha256(b"")),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_sha256_length(self):
        self.assertEqual(len(HashHelper.sha256(b"x")), 32)

    def test_sha1_known(self):
        self.assertEqual(
            HashHelper.to_hex(HashHelper.sha1(b"abc")),
            "a9993e364706816aba3e25717850c26c9cd0d89d")

    def test_sha512_known(self):
        self.assertEqual(
            HashHelper.to_hex(HashHelper.sha512(b"abc")),
            "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2"
            "192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f")

    def test_md5_known(self):
        self.assertEqual(
            HashHelper.to_hex(HashHelper.md5(b"abc")),
            "900150983cd24fb0d6963f7d28e17f72")

    def test_hmac_sha256_known(self):
        d = HashHelper.hmac_sha256(b"key", b"The quick brown fox jumps over the lazy dog")
        self.assertEqual(
            HashHelper.to_hex(d),
            "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8")

    def test_hmac_sha1_known(self):
        d = HashHelper.hmac_sha1(b"key", b"The quick brown fox jumps over the lazy dog")
        self.assertEqual(
            HashHelper.to_hex(d),
            "de7c9b85b8b78aa6bc8a7a36f70a90701c9db4d9")

    def test_hmac_sha512_known(self):
        d = HashHelper.hmac_sha512(b"key", b"The quick brown fox jumps over the lazy dog")
        self.assertEqual(
            HashHelper.to_hex(d),
            "b42af09057bac1e2d41708e48a902e09b5ff7f12ab428a4fe86653c73dd248fb8"
            "2f948a549f7b791a5b41915ee4d1ec3935357e4e2317250d0372afa2ebeeb3a")

    def test_hex_roundtrip(self):
        data = b"\x01\x02\xff\x00"
        self.assertEqual(HashHelper.from_hex(HashHelper.to_hex(data)), data)

    def test_to_hex(self):
        self.assertEqual(HashHelper.to_hex(b"\x01\x02\xff"), "0102ff")

    def test_base64_roundtrip(self):
        data = b"hello world\x00\xff"
        self.assertEqual(HashHelper.from_base64(HashHelper.to_base64(data)), data)

    def test_to_base64(self):
        self.assertEqual(HashHelper.to_base64(b"hello world"), "aGVsbG8gd29ybGQ=")

    def test_pbkdf2_sha256_known(self):
        dk = HashHelper.pbkdf2_sha256("password", b"salt", iterations=1000, dklen=32)
        self.assertEqual(
            HashHelper.to_hex(dk),
            "632c2812e46d4604102ba7618e9d6d7d2f8128f6266b4a03264d2a0460b7dcb3")


class TestSSLHelper(unittest.TestCase):

    def test_constructor_defaults(self):
        h = SSLHelper(cert_file="ca.pem")
        self.assertTrue(h.verify)
        self.assertEqual(h._cert_file, "ca.pem")

    def test_verify_getter_setter(self):
        h = SSLHelper()
        self.assertTrue(h.verify)
        h.verify = False
        self.assertFalse(h.verify)

    def test_wrap_server_without_key_raises(self):
        h = SSLHelper()
        with self.assertRaises(ValueError):
            h.wrap_server_socket(object())


if __name__ == "__main__":
    unittest.main()
