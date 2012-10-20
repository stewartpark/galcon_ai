#!/bin/sh

PYTHON=pypy

if [ -z "$MAP" ] 
then
    MAP=1;
fi
if [ -z "$BOT" ] 
then
    BOT=DualBot;
fi
if [ -z "$TURN" ]
then
    TURN=200
fi

rm -f output.log
java -jar tools/PlayGame-1.2.jar maps/map$MAP.txt 1000 $TURN log.txt "java -jar example_bots/$BOT.jar" "$PYTHON jypbot.py" | java -jar tools/ShowGame-1.2.jar
cat output.log
