#!/bin/sh

PYTHON=pypy

if [ -z "$BOT" ]
then
    BOT=DualBot;
fi

c=0
for i in {1..100}
do
    echo Round $i
    RST=`java -jar tools/PlayGame-1.2.jar maps/map$i.txt 1000 200 log.txt "$PYTHON jypbot.py" "java -jar example_bots/$BOT.jar" 2>&1 | grep "Player 1"`
    if [ -n "$RST" ]
    then
        c=`expr $c + 1`
    else
        echo map$i: lose
    fi
done

echo W/L Rate: $c/100
