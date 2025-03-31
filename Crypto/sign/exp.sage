# sage
__import__('os').environ['TERM'] = 'xterm'

from sage.all import * 
from Crypto.Util.number import *
from functools import reduce
from random import *
from pwn import *
from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES
from hashlib import md5

def inv_shift_right(x:int,bit:int,mask:int = 0xffffffff) -> int:
    tmp = x 
    for _ in range(32//bit):
        tmp = x ^^ tmp >> bit & mask
    return tmp

def inv_shift_left(x:int,bit:int,mask:int = 0xffffffff) -> int:
    tmp = x
    for _ in range(32//bit):
        tmp = x ^^ tmp << bit & mask
    return tmp

def rev_extract(y:int) -> int:
    y = inv_shift_right(y,18)
    y = inv_shift_left(y,15,4022730752)
    y = inv_shift_left(y,7,2636928640)
    y = inv_shift_right(y,11)
    return y

def exp_mt19937(output:list) -> int:
    assert len(output) == 624
    cur_stat = [rev_extract(i) for i in output]
    r = Random()
    r.setstate((3, tuple([int(i) for i in cur_stat] + [624]), None))
    return r.getrandbits(32)

io = remote('39.106.16.204',64393)
io.recvuntil(b':')
aes_cipher = bytes.fromhex(io.recvline().strip().decode())
io.sendlineafter(b':',b'')
msg = []
for _ in range(30000):
    io.recvuntil(b'[+]')
    msg.append(int(io.recvline().strip().decode()))

io.close()
msg = [msg[i:i+2500] for i in range(0,30000,2500)]


d1 = []
for dx in range(12):
    cp = msg[dx]

    mt = matrix(ZZ,21,21)
    for i in range(20):
        mt[i,i] = cp[-1]
        mt[-1,i] = cp[i]
    
    const = 2 ^ 30
    mt[-1,-1] = const
    mt = mt.LLL()

    temp = abs(mt[0,-1])
    assert temp % const == 0

    q0 = temp / const
    e0 = ZZ(cp[-1] % q0)
    p = ZZ((cp[-1] - e0) / q0)

    d1.append(list(map(lambda x: x % p % 256,cp)))

d2 = b''

for dx in range(12):
    ran_output = [bytes_to_long(bytes(d1[dx][i:i+4])) for i in range(0,2496,4)]
    invmul_key = [pow(i,-1,0x101) for i in long_to_bytes(exp_mt19937(ran_output[::-1]))]

    res = []
    for i in range(4):
        res.append(invmul_key[i] * d1[dx][-4 + i] % 0x101)

    assert all(0 <= i < 4 for i in res)
    res.reverse()
    d2 += bytes([reduce(lambda x,y: 4*x+y,res)])
    
print(unpad(AES.new(md5(d2).digest(),AES.MODE_ECB).decrypt(aes_cipher),16).decode())
    

