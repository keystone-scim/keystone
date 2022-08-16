# Contributing to Keystone

### Development using Docker

#### Build the Image

Requirements:

* **A WSL2/MacOS/Linux shell**: You'll need a Linux shell to build and run the container locally.
  A standard Linux/Unix shell includes GNU Make, which is required in order to use the shortcut commands
  in this project's Makefile.
* **Docker**: You'll need a Docker daemon such as the one included with
  [Docker Desktop](https://www.docker.com/products/docker-desktop/). This is required to build the container
  image locally.

To build the image, run the following command:

```shell
make build-image
```

#### Run the Container Locally

In short, you can use the following Make command to run the container locally:

```shell
make docker-run-dev
```

This Make command will expand to the following `docker run` command:

```shell
docker run \
    --rm -it --name scim-2-api-python-dev \
    -p 5001:5001 \
    --mount type=bind,source=$(pwd)/config/dev.yaml,target=/tmp/config.yaml \
    --env CONFIG_PATH=/tmp/config.yaml scim-2-api-python-dev:latest
```

Running the container with the default values will expose the API on port 5001.
You should now be able to inspect the OpenAPI specifications (Swagger docs) opening [http://localhost:5001](http://localhost:5001)
in your browser.

### Development using bare Python

This project uses [Poetry](https://python-poetry.org/).  Installing Poetry alongside
[pyenv](https://github.com/pyenv/pyenv) will make it very easy for you to get started
with local development that doesn't rely on Docker.

After installing Python 3.9 and Poetry, you can follow the instructions above to run
the API locally:

1. Run the following command to spawn a new virtual environment:

   ```shell
   poetry shell
   ```

2. Run the following command to install the project dependencies in the virtual environment:

   ```shell
    poetry install
   ```
   
   This will also install the dev dependencies, which you can use for running the tests. 

3. Running `poetry install` inside the virtual environment also registers scripts and their triggering aliases:
   For this reason, you can run the project using the following command:

   ```shell
   LOG_LEVEL=info CONFIG_PATH=./config/dev.yaml aad-scim2-api
   ```

You should now be able to inspect the OpenAPI specifications (Swagger docs) opening
[http://localhost:5001](http://localhost:5001) in your browser.

### Implementing a Store

Implementing your store is possible implementing the [`BaseStore`](./keystone/store/__init__.py) 
class.  See [`CosmosDbStore`](./keystone/store/cosmos_db_store.py) and
[`MemoryStore`](./keystone/store/memory_store.py) classes for implementation references.
