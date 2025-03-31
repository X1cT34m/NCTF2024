from Crypto.Util.number import *
from os import getenv,urandom
from hashlib import sha256
from random import randint

class ECDSA:
    def __init__(self):
        self.p = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
        self.a = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
        self.b = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
        self.n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
        self.Gx = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
        self.Gy = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
        self.G = (self.Gx,self.Gy)

        self.d = getPrime(232)
        self.Q = self.mul(self.d,self.G)
        assert self.is_on_curve(self.Q)

    def is_on_curve(self, point):
        if point is None:
            return True
        x, y = point
        return (y**2 - x**3 - self.a * x - self.b) % self.p == 0

    def add(self, p1, p2):
        if p1 is None or p2 is None:
            return p1 if p2 is None else p2

        x1, y1 = p1
        x2, y2 = p2

        if x1 == x2 and y1 != y2:
            return None
        if x1 == x2:
            m = (3 * x1 * x1 + self.a) * pow(2 * y1, -1,  self.p) % self.p
        else:
            m = (y2 - y1) * pow((x2 - x1) % self.p, -1, self.p) % self.p
        
        x3 = (m * m - x1 - x2) % self.p
        y3 = (m * (x1 - x3) - y1) % self.p
        return (x3, y3)

    def mul(self, k:int, P:tuple[int,int]):
        if P is None:
            return None
        
        R = None        
        while k > 0:
            if k & 1:
                R = self.add(R, P)
            P = self.add(P,P)
            k >>= 1
        return R

    def sign(self, message):
        while True:
            k = randint(1, self.n - 1)
            P = self.mul(k, self.G)
            if P is None:
                continue
            
            r = P[0] % self.n
            if r == 0:
                continue

            s = (pow(k,-1,self.n) * (int.from_bytes(sha256(message).digest())+ self.d * r)) % self.n
            if s != 0:
                return (r, s)

    def verify(self, m:bytes, r:int,s:int):
        if not (1 <= r < self.n and 1 <= s < self.n):
            return False
        
        u1 = (int.from_bytes(sha256(m).digest()) * pow(s,-1,self.n)) % self.n
        u2 = (r * pow(s,-1,self.n)) % self.n

        if u1 == 0 or u2 == 0:
            return False

        P = self.add(self.mul(u1, self.G), self.mul(u2, self.Q))        
        return P[0] % self.n == r

class RSA:
    def __init__(self,d:int):
        p = getStrongPrime(1024)
        q = getStrongPrime(1024)
        
        assert GCD(d,(p-1)*(q-1)) == 1

        self.N = p * q
        self.d = d
        self.e = pow(d,-1,(p-1)*(q-1))

    def encrypt(self,m:int,idx:int):
        return pow(m,self.e ^ (1 << idx),self.N)
    
def check():
    r,s = list(map(int,input('Give me your signature:').split()))
    if e.verify(f'nctf2024-{urandom(1).hex()}'.encode(),r,s):
        print(f'Congratulations! Here is your flag: {getenv("FLAG")}')
        exit()
    else:
        print('Wrong!')


if __name__=='__main__':
    e = ECDSA()
    print('Can you navigate yourself through QiYun Valley with only the encryption orcale?')

    menu = '''
--- Menu ---
[1] Initialize encryption orcale
[2] Check your signature
[3] Exit'''

    while True:
        print(menu)
        opt = input('Your option:').strip()
        
        if opt=='1':
            print('Generating new public key pair for you...')
            rsa = RSA(e.d ** 4)

            while input("Enter 'e' for encryption or other to exit:").strip() == "e":
                m = int(input('Enter your message:'),16)
                x = int(input('Where do you want to interfere?'))

                print(f'Result:{hex(rsa.encrypt(m,x))[2:]}')

        elif opt=='2':
            check()
        
        elif opt=='3':
            print('Bye~')
            exit()

        else:
            print('Invalid option')





