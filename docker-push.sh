#!/bin/bash
set -ex

docker-compose build

docker login

TAG=$(date '+%Y-%m-%d')

docker tag igrek5151/xman:latest igrek5151/xman:$TAG
docker push igrek5151/xman:latest
docker push igrek5151/xman:$TAG
