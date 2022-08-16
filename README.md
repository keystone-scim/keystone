# Keystone

![GHCR](https://img.shields.io/github/v/release/yuvalherziger/keystone?label=Release&logo=task&logoColor=white&style=flat-square)&nbsp;
![Docker Build](https://img.shields.io/github/workflow/status/yuvalherziger/keystone/Docker%20Build?label=Build&logo=docker&logoColor=white&style=flat-square)&nbsp;
![Unit Tests](https://img.shields.io/github/workflow/status/yuvalherziger/keystone/Unit%20Tests?label=Unit&logo=pytest&logoColor=white&style=flat-square)&nbsp;
![Integration Tests](https://img.shields.io/github/workflow/status/yuvalherziger/keystone/Integration%20Tests?label=Integration&logo=pytest&logoColor=white&style=flat-square)&nbsp;
![License](https://img.shields.io/github/license/yuvalherziger/keystone?label=License&style=flat-square)&nbsp;

<img src="./logo/logo.png" alt="logo" width="200px" />

**Keystone** is a fully containerized lightweight SCIM 2.0 API implementation.

## Getting started

Run the service with zero config to test it:

```shell
# Pull the image:
docker pull yuvalherziger/keystone:latest

# Run the container:
docker run -p 5001:5001 yuvalherziger/keystone:latest
```

See also [Keystone configuration](./config).

**What's Keystone?**

**Keystone** implements the SCIM 2.0 REST API.  If you run your identity management
operations with an identity manager that supports user provisioning (e.g., Azure AD, Okta, etc.),
you can use **Keystone** to persist directory changes. Keystone v0.1.0 supports two practical
persistence layers: Azure Cosmos DB and PostgreSQL.

Key features:

* A compliant [SCIM 2.0 REST API](https://datatracker.ietf.org/doc/html/rfc7644)
  implementation for Users and Groups.
* Stateless container - deploy it anywhere you want (e.g., Kubernetes).
* Pluggable store for users and groups. Current supported storage technologies:
  * Azure Cosmos DB
  * PostgreSQL (>= v.10)
  * In-Memory (for testing purposes only)
* Azure Key Vault bearer token retrieval.
* Extensible stores.

TODO: CITEXT caveat: https://docs.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-extensions

Can't use Cosmos DB or PostgreSQL?  Open an issue and/or consider
[becoming a contributor](./CONTRIBUTING.md).

A containerized, Python-based [SCIM 2.0 API](https://datatracker.ietf.org/doc/html/rfc7644) implementation in asynchronous
Python 3.9, using [asyncio](https://docs.python.org/3/library/asyncio.html)
on top of an [aiohttp](https://docs.aiohttp.org/en/stable/) Server.

This SCIM 2.0 API implementation includes a pluggable user and group store module. Store types are pluggable
in the sense that the REST API is separated from the caching layer, allowing you to extend this project to include any
type of user and group store implementation.  This namely allows you to have the SCIM 2.0 API persist users and groups
in any type of store.

**Please note:** The API is currently experimental.  Please take that into consideration before
integrating it into production workloads.

Currently, the API implements the following stores:

* **Azure Cosmos DB Store**: This store implementation reads and writes to an
  [Azure Cosmos DB](https://docs.microsoft.com/en-us/azure/cosmos-db/introduction) container for users and groups.
* **In-memory Store**: This store implementation reads and writes to an in-memory store.
  Given its ephemeral nature, the in-memory store is meant to be used _strictly_ for development purposes.
  Inherently, the in-memory store shouldn't and cannot be used in a replicated deployment, since
  each node running the container will have its own store.

## Configure the API

See [Keystone Configuration Reference](./config).

You can configure the API in two ways, whilst both can be used in conjunction with one another:

1. **YAML file:** You can mount a volume with a YAML file adhering to the configuration schema (see table below)
   and instruct the container to load the file from a path specified in the `CONFIG_PATH` environment variable.

   The following example uses a Cosmos DB store and loads the API bearer token from an Azure key vault,
   both interacting with their respective Azure service with a managed identity (default credentials):

   ```yaml
   store:
     type: CosmosDB
     cosmos_account_uri: https://mycosmosdbaccount.documents.azure.com:443/
   authentication:
     akv:
       vault_name: mykeyvault
       secret_name: scim2bearertoken
   ```
2. **Environment variables:** You can populate some, all, or none of the configuration keys using environment
   variables.  All configuration keys can be represented by an environment variable by
   the capitalizing the entire key name and replacing the nesting dot (`.`) annotation with
   an underscore (`_`).

   For example, `store.cosmos_account_key` can be populated with the
   `STORE_COSMOS_ACCOUNT_KEY` environment variable in the container the API is running in.

**Please note:** 

| **Key**                                                                           | **Type** | **Description**                                                                      | **Default Value**      |
|-----------------------------------------------------------------------------------|----------|--------------------------------------------------------------------------------------|------------------------|
| store.<br>&nbsp;&nbsp;type                                                        | string   | The persistence layer type. Supported values: `CosmosDB`, `InMemory`                 | `CosmosDB`             |
| store.<br>&nbsp;&nbsp;tenant_id                                                   | string   | Azure Tenant ID, if using a Cosmos DB store with Client Secret Credentials auth.     | -                      |
| store.<br>&nbsp;&nbsp;client_id                                                   | string   | Azure Client ID, if using a Cosmos DB store with Client Secret Credentials auth.     | -                      |
| store.<br>&nbsp;&nbsp;secret                                                      | string   | Azure Client Secret, if using a Cosmos DB store with Client Secret Credentials auth. | -                      |
| store.<br>&nbsp;&nbsp;cosmos_account_uri                                          | string   | Cosmos Account URI, if using a Cosmos DB store                                       | -                      |
| store.<br>&nbsp;&nbsp;cosmos_account_key                                          | string   | Cosmos DB account key, if using a Cosmos DB store with Account Key auth.             | -                      |
| store.<br>&nbsp;&nbsp;cosmos_db_name                                              | string   | Cosmos DB database name, if using a Cosmos DB store                                  | `scim_2_identity_pool` |
| authentication.<br>&nbsp;&nbsp;secret                                             | string   | Plain secret bearer token                                                            | -                      |
| authentication.<br>&nbsp;&nbsp;akv.<br>&nbsp;&nbsp;&nbsp;&nbsp;vault_name         | string   | AKV name, if bearer token is stored in AKV.                                          | -                      |
| authentication.<br>&nbsp;&nbsp;akv.<br>&nbsp;&nbsp;&nbsp;&nbsp;secret_name        | string   | AKV secret name, if bearer token is stored in AKV.                                   | `scim-2-api-token`     |
| authentication.<br>&nbsp;&nbsp;akv.<br>&nbsp;&nbsp;&nbsp;&nbsp;credentials_client | string   | Credentials client type, if bearer token is stored in AKV.                           | `default`              |
| authentication.<br>&nbsp;&nbsp;akv.<br>&nbsp;&nbsp;&nbsp;&nbsp;force_create       | bool     | Try to create an AKV secret on startup, if bearer token to be stored in AKV.         | `false`                |

## Deploy the API

TBA.

## Development

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

This command will the following expanded command:

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
