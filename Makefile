#!/bin/bash

.PHONY: docker-build docker-run docker-all

.DEFAULT_GOAL := docker-all

docker-build:
	docker build -t cli:local image/cli
docker-run:
	docker run -ti cli:local
docker-all: docker-build docker-run
