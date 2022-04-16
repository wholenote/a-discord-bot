#!/bin/sh

cd /home/pi/a-discord-bot

sudo docker stop $(sudo docker ps -q)

git pull

chmod +x docker_image_update.sh

sudo docker build -t monkebot .

sudo docker run -d --env-file server.env --network=host monkebot

sudo docker rm $(docker ps -a -f status=exited -q)

sudo docker image prune -f