#!/bin/sh
if [ -z "$MAP" ] 
then
    MAP=1;
fi
if [ -z "$BOT" ] 
then
    BOT=DualBot;
fi

rm -f output.log
java -jar tools/PlayGame-1.2.jar maps/map$MAP.txt 1000 200 log.txt "python jypbot.py" "java -jar example_bots/$BOT.jar" | java -jar tools/ShowGame-1.2.jar
cat output.log
