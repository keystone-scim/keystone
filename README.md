<div align="center">
    <img src="./logo/logo.png" alt="logo" width="200px" />
    <h1>Keystone</h1>
    <a href="https://github.com/keystone-scim/keystone/releases">
        <img src="https://img.shields.io/github/v/release/keystone-scim/keystone?label=Release&logo=task&logoColor=white&style=flat-square" alt="GHCR" />
    </a>
    <a href="https://github.com/keystone-scim/keystone/actions/workflows/docker_build.yaml">
        <img src="https://img.shields.io/github/workflow/status/keystone-scim/keystone/Docker%20Build?label=Build&logo=docker&logoColor=white&style=flat-square" alt="Docker Build" />
    </a>
    <a href="https://github.com/keystone-scim/keystone/actions/workflows/unit_tests.yaml">
        <img src="https://img.shields.io/github/workflow/status/keystone-scim/keystone/Unit%20Tests?label=Unit&logo=pytest&logoColor=white&style=flat-square" alt="Unit Tests" />
    </a>
    <a href="https://github.com/keystone-scim/keystone/actions/workflows/integration_tests.yaml">
        <img src="https://img.shields.io/github/workflow/status/keystone-scim/keystone/Integration%20Tests?label=Integration&logo=pytest&logoColor=white&style=flat-square" alt="Integration Tests" />
    </a>
    <a href="./LICENSE">
        <img src="https://img.shields.io/github/license/keystone-scim/keystone?label=License&style=flat-square" alt="License" />
    </a>
    <a href="https://keystone-scim.github.io">
        <img src="https://img.shields.io/github/workflow/status/keystone-scim/keystone-scim.github.io/Publish/main?color=magenta&label=Docs&logo=read%20the%20docs&style=flat-square" alt="License" />
    </a>
    <hr />
</div>

**Keystone** is a fully containerized lightweight SCIM 2.0 API implementation.

## Getting Started

Run the container with zero config to test it:

```shell
# Pull the image:
docker pull ghcr.io/keystone-scim/keystone:latest

# Run the container:
docker run -it \
  -p 5001:5001 \ 
  -e AUTHENTICATION_SECRET=supersecret \
  ghcr.io/keystone-scim/keystone:latest
```

Read the [Keystone documentation](https://keystone-scim.github.io) to understand how you can configure Keystone with
its different backends.

**What's Keystone?**

**Keystone** implements the SCIM 2.0 REST API.  If you run your identity management
operations with an identity manager that supports user provisioning (e.g., Azure AD, Okta, etc.),
you can use **Keystone** to persist directory changes. Keystone v0.1.0 supports two
persistence layers: PostgreSQL and Azure Cosmos DB.

<div align="center">
    <img src="./logo/how-it-works.png" alt="logo" />
</div>


Key features:

* A compliant [SCIM 2.0 REST API](https://datatracker.ietf.org/doc/html/rfc7644)
  implementation for Users and Groups.
* Stateless container - deploy it anywhere you want (e.g., Kubernetes) and bring your own storage.
* Pluggable store for users and groups. Current supported storage technologies:
  * [Azure Cosmos DB](https://docs.microsoft.com/en-us/azure/cosmos-db/introduction)
  * [PostgreSQL](https://www.postgresql.org) (version 10 or higher)
  * [MongoDB](https://www.mongodb.com/docs/) (version 3.6 or higher)
* Azure Key Vault bearer token retrieval.
* Extensible store: Can't use Cosmos DB or PostgreSQL?  Open an issue and/or consider
[becoming a contributor](./CONTRIBUTING.md).

## Configure the API

See [Keystone Documentation](https://keystone-scim.github.io).

## Development

Please see the [Contribution Guide](./CONTRIBUTING.md) to get started.
