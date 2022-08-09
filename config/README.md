# Keystone Configuration

This page outlines the possible configurations that
a Keystone container supports.

## YAML File or Environment Variables?

The short answer: You can use either a YAML file, environment variables,
or **a combination of both**.

You can populate some, all, or none of the configuration keys using environment
variables. All configuration keys can be represented by an environment variable by
the capitalizing the entire key name and replacing the nesting dot (`.`) annotation with
an underscore (`_`).

For example, `store.cosmos_account_key` can be populated with the
`STORE_COSMOS_ACCOUNT_KEY` environment variable in the container
the API is running in.

## Configure Keystore with Environment Variables

| **VARIABLE**                                                                      | **Type** | **Description**                                                                      | **Default Value**      |
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

## Configure Keystone with a YAML File


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