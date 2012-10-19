#!/bin/sh

MAP=map3
BOT=DualBot
rm -f output.log
java -jar tools/PlayGame-1.2.jar maps/$MAP.txt 1000 200 log.txt "python jypbot.py" "java -jar example_bots/$BOT.jar" | java -jar tools/ShowGame-1.2.jar
cat output.log
