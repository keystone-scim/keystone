#!make

VERSION ?= $(shell git describe --tags --exact-match 2>/dev/null || git rev-parse --abbrev-ref HEAD)
DOCKER_BIN := docker
PYTHON_BIN := python
POETRY_BIN := poetry
IMAGE_NAME := scim-2-api-python
IMAGE_TAG := latest
AZ_CLI_BIN := az
PORT := 5001

.PHONY: build-image
build-image:
	$(DOCKER_BIN) build -t $(IMAGE_NAME):$(IMAGE_TAG) .

.PHONY: unit-tests
unit-tests: export CONFIG_PATH=./config/unit-tests.yaml
unit-tests:
	$(POETRY_BIN) run pytest tests/unit -p no:warnings --cov=keystone --asyncio-mode=strict

.PHONY: integration-tests-mem-store
integration-tests-mem-store: export CONFIG_PATH=./config/integration-tests-memory-store.yaml
integration-tests-mem-store:
	$(POETRY_BIN) run pytest tests/integration -p no:warnings --verbose --asyncio-mode=strict ; \
	$(POETRY_BIN) run tests/integration/scripts/cleanup.py

.PHONY: integration-tests-cosmos-store
integration-tests-cosmos-store: export CONFIG_PATH=./config/integration-tests-cosmos-store.yaml
integration-tests-cosmos-store: export STORE_COSMOS_DB_NAME=scim_int_tsts_$(shell date +%s)
integration-tests-cosmos-store:
	$(POETRY_BIN) run pytest tests/integration -p no:warnings --verbose --asyncio-mode=strict ; \
	$(POETRY_BIN) run tests/integration/scripts/cleanup.py

.PHONY: security-tests
security-tests:
	$(POETRY_BIN) run bandit -r ./keystone

.PHONY: docker-run-dev
docker-run-dev:
	 $(DOCKER_BIN) run \
	 --rm -it --name $(IMAGE_NAME)-dev -p $(PORT):$(PORT) \
	 --mount type=bind,source="$(shell pwd)"/config/dev.yaml,target=/tmp/config.yaml \
	 --env CONFIG_PATH=/tmp/config.yaml $(IMAGE_NAME):$(IMAGE_TAG)

.PHONY: build-on-mac
build-on-mac:
	$(DOCKER_BIN) buildx build --platform linux/amd64 \
	-t $(IMAGE_NAME):$(IMAGE_TAG) .
