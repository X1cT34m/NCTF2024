__import__('os').environ['TERM'] = 'xterm'

from pwn import *
from sage.all import *
from time import time
from hashlib import sha256

# io = remote('39.106.16.204',10645)

io = remote('39.106.16.204',26786)
# io = process(['python3','task.py'])

nls = []
els = []

recv_hexint = lambda: int(io.recvline().strip().decode(),16)

t0 = time()

for _ in range(10):
    io.sendlineafter(b'option:',b'1')
    #decipher N via GCD

    numls = []
    for i in range(9):
        msg = int(1 << (i + 1)).to_bytes(2,'big')
        io.sendlineafter(b'exit:',b'e')
        io.sendlineafter(b'message:',msg.hex().encode())
        io.sendlineafter(b'interfere?',b'0')
        io.recvuntil(b'Result:')
        numls.append(int(io.recvline().strip().decode(),16))

    gcdls = []
    for i in range(1,9):
        gcdls.append(numls[0] ^ (i+1) - numls[i])

    n = gcd(gcdls)
    nls.append(n)
    print(f'n #{_} = {n}')

    #decipher e via fault injection of e

    orcale_msg = 3

    io.sendlineafter(b'exit:',b'e')
    io.sendlineafter(b'message:',int(orcale_msg).to_bytes(1,'big').hex().encode())
    io.sendlineafter(b'interfere?',b'2048')
    io.recvuntil(b'Result:')
    basis = recv_hexint() * pow(orcale_msg, -2^2048, n) % n #basis, = pow(m,e,n)    

    e_rng = [0] * 2048

    for i in range(2048):
        io.sendlineafter(b'exit:',b'e')
        io.sendlineafter(b'message:',int(orcale_msg).to_bytes(1,'big').hex().encode())
        io.sendlineafter(b'interfere?',str(i).encode())
        io.recvuntil(b'Result:')
        
        temp = recv_hexint()
        multiplier = pow(orcale_msg,2^i,n)

        if temp == basis * multiplier % n: #0 -> 1, original = 0
            e_rng[i] = 0
        else: #1 -> 0, original = 1
            assert temp == basis * pow(multiplier,-1,n) % n #ensure
            e_rng[i] = 1

    e_res = int(''.join(str(i) for i in e_rng)[::-1],2)
    assert pow(orcale_msg,e_res,n) == basis
    els.append(e_res)

    print(f'e #{_} = {e_res}')
    print(f'Time elasped: {time()-t0:.2f}s')
    io.sendlineafter(b'exit:',b'')


const = 2^1024
mt = matrix.diagonal(ZZ,nls + [0]).dense_matrix()
mt[-1] = els + [const]
mt = mt.LLL()

temp = abs(mt[0,-1])
assert temp % const == 0
d = ZZ(temp / const)

x = d.nth_root(4)
E = EllipticCurve(Zmod(0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF),[0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC,0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93])
n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
assert E.order() == n

G = E((0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7,0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0))
m0 = int.from_bytes(sha256('nctf2024-00'.encode()).digest(),'big')

while True:
    k = int(time() * 1000) #should be smaller than n
    P = k * G
    r = int(P.xy()[0]) % n
    s = (pow(k,-1,n) * (m0 + x*r)) % n
    if r != 0 and s != 0:
        break

send = f'{r} {s}'.encode()
while True:
    io.sendlineafter(b'option:',b'2')
    io.sendlineafter(b':',send)
    msg = io.recvline()
    if b'flag' in msg:
        print(msg.decode())
        break

io.close()
