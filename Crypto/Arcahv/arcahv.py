from Crypto.Util.number import *
from os import urandom,getenv
from functools import reduce
from Crypto.Cipher import AES

class LCG:
    def __init__(self,seed:int) -> None:
        self.p = getPrime(1024)
        self.a = getPrime(1023)
        self.b = getPrime(1023)
        self.status = seed

    def next(self) -> int:
        ret = self.status
        self.status = (self.status * self.a + self.b) % self.p
        return ret
    
def crystal_trick(m:bytes) -> bytes:
    m = bytearray(m)
    for i in range(len(m)):
        m[i] = reduce(lambda x,y: x^y^urandom(1)[0],m[:i],m[i])
    return m

class RSA:
    def __init__(self):
        p = getStrongPrime(1024)
        q = getStrongPrime(1024)
        self.p = p
        self.N = p * q
        self.e = 65537
        self.d = pow(self.e, -1, (p-1)*(q-1))

    def encrypt(self,m:int) -> int:
        return pow(m,self.e,self.N)
    
    def decrypt(self,c:int) -> int:
        return pow(c,self.d,self.N) 

class MyRSA1(RSA):
    def encrypt(self,m:bytes) -> bytes:
        return super().encrypt(int.from_bytes(m)).to_bytes(256)
    
    def decrypt(self,c:bytes) -> bytes:
        return super().decrypt(int.from_bytes(c)).to_bytes(256)

class MyRSA2(RSA):
    def encrypt(self,m:bytes) -> bytes:
        return pow(int.from_bytes(m),self.e,self.N).to_bytes(256,'little')
    
    def decrypt(self,c:bytes) -> bytes:
        m = pow(int.from_bytes(c),self.d,self.N).to_bytes(256,'little')
        print('Hibiscus is here to trick your decryption result!!')
        return crystal_trick(m)

menu = '''
Welcome to NCTF 2025 arcahv challenge!

--- Menu ---
[1] View encrypted flag and hint
[2] Play with the decryption orcale
[3] Get some random numbers for fun
[4] Exit

Your Option > '''


if __name__=='__main__':
    print('Loading, please wait...')
    
    # flag = open('flag.txt').read().strip().encode()
    flag = getenv('FLAG').encode()
    attempts = 75
    r1 = MyRSA1()
    r2 = MyRSA2()
    hint1 = r2.encrypt(r1.p.to_bytes(128))

    key = urandom(16)
    hint2 = AES.new(key,AES.MODE_ECB).encrypt(r1.N.to_bytes(256))

    def flag_and_hint():
        print(f'Encrypted flag: {r1.encrypt(flag).hex()}')
        print(f'Hint1: {hint1.hex()}')
        print(f'Hint2: {hint2.hex()}')

    def rsachal(): 
        global attempts

        print("Since you didn't v Hibiscus 50 on crazy thursday, Hibiscus decided to do some trick on your decryption result!")
        print(f'Your pubkey:({hex(r2.N)[2:]},{hex(r2.e)[2:]})')

        while attempts > 0:
            if input('Do you still want to try decryption(y/[n])?') != 'y':
                break

            c = bytes.fromhex(input(f'You have {attempts} remaining access to decryption orcale!\nYour ciphertext(in hex):'))
            print(f'Result: {r2.decrypt(c).hex()}')
            attempts -= 1
        
        if attempts == 0:
            print('Unfortunately, you are out of decryption attempts! Come back again on nctf2026 ~')

    
    def lcgchal():
        lcg = LCG(int.from_bytes(key))

        print('Tempering with LCG generator, please wait...')
        while urandom(1)[0] & 0xff:
            lcg.next()
        
        hexnums = ''.join(hex(lcg.next())[2:] for _ in range(5))
        if len(hexnums) % 16:
            hexnums = hexnums.zfill((len(hexnums) // 16 + 1) * 16)
        
        idx = 0
        while input('Do you want another unsigned long long number(y/[n])?') == 'y':
            print(int(''.join(hexnums[idx:idx+16]),16))
            idx = (idx + 16) % len(hexnums)

    def bye():
        print('Hope you have fun during the challenge XD:)')
        exit(0)

    fundc = {1:flag_and_hint,2:rsachal,3:lcgchal,4:bye}

    while True:
        opt = input(menu)
        if len(opt) == 0 or opt not in '1234':
            opt = '4'
        fundc[int(opt)]()
