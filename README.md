# Azure AD SCIM 2.0 API

A containerized, Python-based [SCIM 2.0 API](https://datatracker.ietf.org/doc/html/rfc7644) implementation in asynchronous
Python 3.9, using [asyncio](https://docs.python.org/3/library/asyncio.html)
and [aiohttp](https://docs.aiohttp.org/en/stable/).

This SCIM 2.0 API implementation includes a pluggable user and group store module for
[Azure Active Directory](https://azure.microsoft.com/en-us/services/active-directory/). Other store types are pluggable
in the sense that the REST API is separated from the caching layer, allowing you to extend this project to include any
type of user and group store implementation.  This namely allows you to have the SCIM 2.0 API persist users and groups
in any type of store.

**Table of Contents:**

- [Build the Image](#build-the-image)
- [Push the Image to ACR](#push-the-image-to-acr)
- [Configure the API](#configure-the-api)
- [Deploy the API](#deploy-the-api)
- [Development](#development)
  * [Development using Docker](#development-using-docker)
  * [Development using bare Python](#development-using-bare-python)

## Build the Image

TBA.

## Push the Image to ACR

You can automate the publishing of the container image to an
[Azure Container Registry (ACR)](https://azure.microsoft.com/en-us/services/container-registry/) using Terraform or
another IaC of your choice.

Instructions TBA.

## Configure the API

TBA.

## Deploy the API

TBA.

## Development

### Development using Docker

TBA.

### Development using bare Python

TBA.
