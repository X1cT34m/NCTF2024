from random import *
import time
import pyfiglet
import os
import hashlib
text = "X1crypsc"
ascii_art = pyfiglet.figlet_format(text)
print(ascii_art)
time.sleep(1)
print('[+]I want to play a game.\n')
time.sleep(1)
print('[+]If you win the game, I will give you a gift:)\n')
time.sleep(1)
print('[+]But try to beat the monster first:)\n')
time.sleep(1)
print('[+]Good luck!\n')
print('[+]You got a weapon!\n')
damage_rng = ()
def regenerate_damage():
    global damage_rng
    base = getrandbits(16)
    add = getrandbits(16)
    damage_rng = (base ,base + add)
monster_health = getrandbits(64)
menu = '''
---Options---
[W]eapon
[A]ttack
[E]xit
'''
regenerate_damage()
print(menu)
HP = 3
while True:
    if monster_health <= 0:
        print('[+] Victory!!!')
        break
    if HP <= 0:
        print('[!] DEFEAT')
        exit(0)
    print(f'[+] Monster current HP:{monster_health}')
    print(f'[+] Your current HP: {HP}')
    opt = input('[-] Your option:')
    if opt == 'W':
        print(f'[+] Current attack value: {damage_rng[0]} ~ {damage_rng[1]}')
        if input('[+] Do you want to refresh the attack profile of the weapon([y/n])?') == 'y':
            regenerate_damage()
            print(f'[+] New weapon attack value: {damage_rng[0]} ~ {damage_rng[1]}')
    elif opt == 'A':
        print('[+] The monster sensed of an imminent danger and is about to teleport!!\n')
        print('[+] Now you have to aim at the monster\'s location to hit it!\n')
        print('[+]Input format: x y\n')
        x,y = map(int,input(f'[-] Provide the grid you\'re willing to aim:').split())
        if [x,y] ==  [randrange(2025),randrange(2025)]:
            dmg = min(int(randint(*damage_rng) ** (Random().random() * 8)),monster_health)
            print(f'[+] Decent shot! Monster was hevaily damaged! Damage value = {dmg}')
            monster_health -= dmg
        else:
            print("[+] Your bet didn't pay off, and the monster presented a counterattack on you!")
            HP -= 1     
    elif opt == 'E':
        print('[+] Bye~')
        exit(0)
    else:
        print('[!] Invalid input')
print('[+]Well done! You won the game!\n')
print('[+]And here is your gift: you got a chance to create a time capsule here and we\'ll keep it for you forever:)\n')
keep_dir = '/app/user_file/'
class File:
    def __init__(self):
        os.makedirs('user_file', exist_ok=True)
    def sanitize(self, filename):
        if filename.startswith('/'):
            raise ValueError('[!]Invalid filename')
        else:
            return filename.replace('../', '')
    def get_path(self, filename):
        hashed = hashlib.sha256(filename.encode()).hexdigest()[:8]
        sanitized = self.sanitize(filename)
        return os.path.join(keep_dir, hashed, sanitized)
    def user_input(self):
        while True:
            filename = input('[-]Please enter the file name you want to create: ')
            data = []
            while True:
                line = input('[-]Now write something into the file (or type "exit" to finish writing): ')
                if line.lower() == 'exit':
                    break
                data.append(line)
                another_line = input('[-]Write in another line? [y/n]: ')
                if another_line.lower() != 'y':
                    break
            try:
                path = self.get_path(filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    for line in data:
                        f.write(line)
                        f.write('\n')
                print(f'[+]Your file has been successfully saved at {path}, we promise we\'ll never lose it :)')
            except:
                print(f'[+]Something went wrong, please try again.')
            while True:
                ask = input('[-]Create more files? [y/n]: ')
                if ask.lower() == 'y':
                    break
                elif ask.lower() == 'n':
                    exit(0)
                else:
                    print('[!]Invalid input, please try again.\n')
file = File()
file.user_input()
exit(0)
