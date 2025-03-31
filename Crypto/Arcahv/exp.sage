__import__('os').environ['TERM'] = 'xterm'

from sage.all import *
from pwn import *
from Crypto.Util.number import *
from Crypto.Cipher import AES

def hexify_send(num:int) -> bytes:
    return long_to_bytes(num).hex().encode()

io = remote('39.106.16.204',28575)
# io = process(['python3','arcahv.py'])


io.sendlineafter(b'>',b'1')

io.recvuntil(b':')
enc_flag = int(io.recvline().strip().decode(),16)
io.recvuntil(b':')
enc_hint = int.from_bytes(bytes.fromhex(io.recvline().strip().decode()),'little')
io.recvuntil(b':')
enc_hint2 = bytes.fromhex(io.recvline().strip().decode())

# RSA LSB Orcale

m = enc_hint
omit_count = 127
io.sendlineafter(b'>',b'2')
io.recvuntil(b'(')
rn = int(io.recvuntil(b',',drop=True).strip().decode(),16)
re = int(io.recvuntil(b')',drop=True).strip().decode(),16)

upper_bound = reduce(lambda x,y:floor(x/256),range(omit_count),rn)

lower_bound = 0
single_mul = pow(256,re,rn)
inv = pow(rn,-1,256)

m = m * pow(single_mul,omit_count,rn) % rn

for i in range(75):
    m = int(m * single_mul % rn)
    
    io.sendlineafter(b'?',b'y')
    io.sendlineafter(b':',hexify_send(m))
    io.recvuntil(b':')
    this = int(io.recvline().strip().decode()[:2],16)

    k = int(-this * inv % 256)
    ttl = (upper_bound - lower_bound) / 256

    lower_bound += ceil(k * ttl)
    upper_bound = lower_bound + floor(ttl)

res_pp = lower_bound

# LCG

io.sendlineafter(b'>',b'3')
ls = []
for _ in range(80):
    io.sendlineafter(b'?',b'y')
    ls.append(int(io.recvline().strip().decode()))


hexstr = ''.join(hex(i)[2:].zfill(16) for i in ls)
lcgnums = [int(hexstr[i:i+256],16) for i in range(0,len(hexstr),256)]


A = [lcgnums[i+1]-lcgnums[i] for i in range(4)]
p = gcd(A[1]^2 - A[2]*A[0],A[2]^2 - A[3]*A[1])

if not isPrime(p):
    p = factor(p)[-1][0]

assert isPrime(p)

a = int(A[1] * int(pow(A[0],-1,p)) % p)
b = int((lcgnums[1] - a * lcgnums[0]) % p)

cur = Zmod(p)(lcgnums[0])
count = 0
while int(cur).bit_length() > 128:
    cur = (cur - b) * pow(a,-1,p)
    count += 1


key = int(cur).to_bytes(16,'big')

res_n = int.from_bytes(AES.new(key,AES.MODE_ECB).decrypt(enc_hint2),'big')

# Coppersmith

P.<x> = Zmod(res_n)[]
f = res_pp + x
rt = f.small_roots(X=2^453,beta=0.4)[0]

p0 = int(res_pp + rt)

assert res_n % p0 == 0
q0 = res_n // p0

d0 = int(pow(65537,-1,(p0-1)*(q0-1)))
print(long_to_bytes(int(pow(enc_flag,d0,res_n))))
