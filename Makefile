#!make

VERSION ?= $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --abbrev-ref HEAD)
DOCKER_BIN := docker
PYTHON_BIN := python
POETRY_BIN := poetry
IMAGE_NAME := azure-ad-scim-2-api
IMAGE_TAG := latest
AZ_CLI_BIN := az

.PHONY: build-image
build-image:
	$(DOCKER_BIN) build -t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: unit-tests
unit-tests: export CONFIG_PATH=./config/tests.yaml
unit-tests:
	$(POETRY_BIN) run pytest tests --asyncio-mode=strict

.PHONY: version
version:
	echo $(VERSION)

