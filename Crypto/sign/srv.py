from Crypto.Util.number import *
from util import *
from os import getenv
from Crypto.Util.Padding import pad
from random import Random
from Crypto.Cipher import AES
from hashlib import md5

string = open('secret.txt').read().strip().encode()
flag = getenv('FLAG').encode()

if __name__=='__main__':
    Keys = []
    for m in string:
        f = FHE()
        s = long_to_bytes(Random().getrandbits(20000))
        for i in s[4:]:
            Keys.extend(f.encrypt([i]))

        for i in s[:4]:
            Keys.extend(f.encrypt([i * (m & 0x03) % 0x101]))
            m >>= 2
        
    assert len(Keys) == 30000

    print(f'[+] Your ciphertext: {AES.new(md5(string).digest(),AES.MODE_ECB).encrypt(pad(flag,16)).hex()}')
    input(f'[+] The keys to retrieve the global internet connection are as follows:')
    for i in range(30000):
        print(f'[+] {Keys[i]}')
