from os import urandom
from Crypto.Util.number import *

def getrandint(n:int):
    return int.from_bytes(urandom(n//8+1)) % pow(2,n)

class FHE:
    def __init__(self):
        self.p = getPrime(77)
        self.pubkeys = []
        for _ in range(16):
            self.pubkeys.append(self.p * getrandint(177) + (getrandint(17) << 8))

    def encrypt(self,msg:list[int] | bytes):
        result = []
        for m in msg:
            tmp = 0
            shuffle_base = urandom(16)
            for i in shuffle_base:
                x,y = divmod(i,16)
                tmp += x*self.pubkeys[y] + y*self.pubkeys[x]
            result.append(tmp + m)
        return result
