#!/bin/sh
echo $FLAG > /home/ctf/flag
unset FLAG
/home/ctf/pwn &> /dev/null &
sleep infinity
