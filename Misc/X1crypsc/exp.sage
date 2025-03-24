__import__('os').environ['TERM'] = 'xterm'

from Crypto.Util.number import *
from pwn import *
from sage.all import *
from random import *
from time import time
import string
io = remote('x.x.x.x',x)

io.recvuntil(b'Monster current HP:')
monster_hp = int(io.recvline().strip().decode())

whatls = []
whatls.extend(int(i) for i in bin(monster_hp)[2:].zfill(64))

io.sendlineafter(b'option:',b'W')
io.recvuntil(b':')
n1 = int(io.recvuntil(b'~',drop=True).strip().decode())
n2 = int(io.recvline().strip().decode()) - n1
whatls.extend(int(i) for i in bin(n1)[2:].zfill(16))
whatls.extend(int(i) for i in bin(n2)[2:].zfill(16))

io.sendlineafter(b'?',b'y')
io.recvuntil(b':')
n1 = int(io.recvuntil(b'~',drop=True).strip().decode())
n2 = int(io.recvline().strip().decode()) - n1
whatls.extend(int(i) for i in bin(n1)[2:].zfill(16))
whatls.extend(int(i) for i in bin(n2)[2:].zfill(16))

for _ in range(620):
    io.sendlineafter(b'option:',b'W')
    io.sendlineafter(b'?',b'y')
    io.recvuntil(b':')
    n1 = int(io.recvuntil(b'~',drop=True).strip().decode())
    n2 = int(io.recvline().strip().decode()) - n1
    whatls.extend(int(i) for i in bin(n1)[2:].zfill(16))
    whatls.extend(int(i) for i in bin(n2)[2:].zfill(16))

weapon_data = [int(''.join(map(str,whatls[-32:-16])),2),int(''.join(map(str,whatls[-16:])),2)]
weapon_data[1] += weapon_data[0]

'''
# map a linear transformation matrix
# compute for first time only, afterwards comment this section for memory & time conservation
mt = []

for i in range(19968):
    f_stats = [0] * 19968
    f_stats[i] = 1

    state = [int(''.join(map(str,f_stats[i*32:(i+1)*32])),2) for i in range(624)]
    
    r = Random()
    r.setstate((3,tuple(state+[624]),None))
    
    vc = []
    vc.extend(int(i) for i in bin(r.getrandbits(64))[2:].zfill(64))
    for _ in range(622): # 624 - 2 = 622
        vc.extend(int(i) for i in bin(getrandbits(16))[2:].zfill(16))
        vc.extend(int(i) for i in bin(getrandbits(16))[2:].zfill(16))

    mt.append(vc)

save(mt,'mt.sobj')
'''

t0 = time()
mt = load('mt.sobj') #matrix(GF(2),...)
resvec = vector(GF(2),whatls)
init = mt.solve_left(resvec)

impl_state = [int(''.join(map(str,init[i*32:(i+1)*32])),2) for i in range(624)]

rn = Random()
rn.setstate((3,tuple(impl_state+[624]),None))

for _ in range(1244): # 622*2
    rn.getrandbits(16)

while True:
    x_grid = rn.randrange(2025)
    y_grid = rn.randrange(2025)
    io.sendlineafter(b'option:',b'A')
    io.sendlineafter(b'aim:',f'{x_grid} {y_grid}'.encode())
    rn.randint(weapon_data[0],weapon_data[1])
    io.recvline()
    if b'Victory' in io.recvline():
        break
io.interactive()
