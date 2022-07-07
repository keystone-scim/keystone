#!make

VERSION ?= $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --abbrev-ref HEAD)
DOCKER_BIN := docker
PYTHON_BIN := python
POETRY_BIN := poetry
IMAGE_NAME := azure-ad-scim-2-api
IMAGE_TAG := latest
AZ_CLI_BIN := az
PORT := 5001

.PHONY: build-image
build-image:
	$(DOCKER_BIN) build -t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: unit-tests
unit-tests: export CONFIG_PATH=./config/tests.yaml
unit-tests:
	$(POETRY_BIN) run pytest tests --verbose --cov=azure_ad_scim_2_api --asyncio-mode=strict

.PHONY: security-tests
security-tests:
	$(POETRY_BIN) run bandit -r ./azure_ad_scim_2_api

.PHONY: docker-run-dev
docker-run-dev:
	 $(DOCKER_BIN) run \
	 --rm -it --name $(IMAGE_NAME)-dev -p $(PORT):$(PORT) \
	 --mount type=bind,source="$(shell pwd)"/config/dev.yaml,target=/tmp/config.yaml \
	 --env CONFIG_PATH=/tmp/config.yaml $(IMAGE_NAME):$(IMAGE_TAG)
