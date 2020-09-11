#!/bin/bash
set -ex

COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker-compose build --no-cache

docker login

TAG=$(date '+%Y-%m-%d')

docker tag igrek5151/xman:latest igrek5151/xman:$TAG
docker push igrek5151/xman:latest
docker push igrek5151/xman:$TAG
