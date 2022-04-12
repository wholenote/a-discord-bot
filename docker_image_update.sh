#!/bin/sh

cd ~/a-discord-bot

sudo docker stop $(sudo docker ps -q)

git pull

sudo docker build -t monkebot .

sudo docker run -d --env-file server.env --network=host monkebot

sudo docker rm $(docker ps -a -f status=exited -q)

sudo docker image prune -f