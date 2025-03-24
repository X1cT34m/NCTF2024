#!/bin/bash

echo $FLAG > /flag
unset FLAG

chown ctf:ctf /flag
chmod 000 /flag

su -p ctf -c "/opt/java/openjdk/bin/java -jar /app/H2Revenge.jar"
