#!/bin/bash

.PHONY: docker-build docker-run docker-all

.DEFAULT_GOAL := docker-all

docker-build:
	docker build -t installer:local image/installer
docker-run:
	docker run -ti installer:local
docker-all: docker-build docker-run
