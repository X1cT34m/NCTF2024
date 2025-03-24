from binascii import hexlify
import argon2
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import string

key_prefix = b"4ZF1SFqBlIUma"
salt = b"This is a non-random salt for sshx.io, since we want to stretch the security of 83-bit keys!"
time_cost = 2
memory_cost = 19 * 1024
parallelism = 1
hash_len = 16

for i in string.printable:
    key = key_prefix + i.encode()
    raw_hash = argon2.low_level.hash_secret_raw(
        secret=key,
        salt=salt,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
        hash_len=hash_len,
        type=argon2.low_level.Type.ID
    )

    iv = bytes([0] * 16)

    plaintext = bytes([0] * 16)

    cipher = Cipher(
        algorithms.AES(raw_hash),
        modes.CTR(iv),
        backend=default_backend()
    )

    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    if ciphertext.hex() == "57c23b95e820aa7e89b41317cc2a5906":
        print(key.decode())
