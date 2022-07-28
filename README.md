# Python SCIM 2.0 API

![Build](https://github.com/yuvalherziger/scim-2-api-python/actions/workflows/build.yaml/badge.svg?branch=main)
![Tests](https://github.com/yuvalherziger/scim-2-api-python/actions/workflows/tests.yaml/badge.svg?branch=main)

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

**Table of Contents:**

- [Build the Image](#build-the-image)
- [Push the Image to ACR](#push-the-image-to-acr)
- [Configure the API](#configure-the-api)
- [Deploy the API](#deploy-the-api)
- [Development](#development)
  * [Development using Docker](#development-using-docker)
  * [Development using bare Python](#development-using-bare-python)
  * [Implementing a Store](#implementing-a-store)

## Build the Image

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

## Configure the API

**Please note:** All configuration keys can be represented by an environment variable by
the capitalizing the entire key name and replacing the nesting dot (`.`) annotation with
an underscore (`_`). For example, `store.client_secret` can be populated with the
`STORE_CLIENT_ID` environment variable in the container the API is running in.

| **Key**                                                              | **Description**                                                                      | **Default Value**      |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|------------------------|
| `store.type` (string)                                                | The persistence layer type. Supported values: `CosmosDB`, `InMemory`                 | `CosmosDB`             |
| `store.tenant_id` (string)                                           | Azure Tenant ID, if using a Cosmos DB store with Client Secret Credentials auth.     | -                      |
| `store.client_id` (string)                                           | Azure Client ID, if using a Cosmos DB store with Client Secret Credentials auth.     | -                      |
| `store.secret` (string)                                              | Azure Client Secret, if using a Cosmos DB store with Client Secret Credentials auth. | -                      |
| `store.cosmos_account_uri` (string)                                  | Cosmos Account URI, if using a Cosmos DB store                                       | -                      |
| `store.cosmos_account_key` (string)                                  | Cosmos DB account key, if using a Cosmos DB store with Account Key auth.             | -                      |
| `store.cosmos_db_name` (string)                                      | Cosmos DB database name, if using a Cosmos DB store                                  | `scim_2_identity_pool` |
| `authentication.azure_key_vault.vault_name` (string)                 | AKV name, if bearer token is stored in AKV.                                          | -                      |
| `authentication.azure_key_vault.secret_name` (string)                | AKV secret name, if bearer token is stored in AKV.                                   | `scim-2-api-token`     |
| `authentication.azure_key_vault.credentials_client` (string)         | Credentials client type, if bearer token is stored in AKV.                           | `default`              |
| `authentication.azure_key_vault.create_secret_if_not_present` (bool) | Try to create an AKV secret on startup, if bearer token to be stored in AKV.         | `false`                |
| `authentication.secret` (string)                                     | Plain secret bearer token                                                            | -                      |
| `authentication.azure_key_vault.vault_name` (string)                 | AKV name, if bearer token is stored in AKV.                                          | -                      |


## Deploy the API

TBA.

## Development

### Development using Docker

TBA.

### Development using bare Python

TBA.

### Implementing a Store

TBA.