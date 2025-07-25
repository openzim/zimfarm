# Zimfarm Backend: v1 to v2 Migration Guide

This document outlines the major changes between Zimfarm Backend v1 (dispatcher/backend) and v2 (current backend directory).

## Overview

Zimfarm Backend v2 represents a significant modernization of the codebase, migrating from Flask to FastAPI and updating to modern Python practices and dependencies.

## Major Changes

### 1. Web Framework Migration

**v1 (Flask):**
- Uses Flask
- Traditional WSGI application
- Manual error handling with custom exception classes

**v2 (FastAPI):**
- Uses FastAPI
- ASGI application with uvicorn server
- Automatic request validation and error handling with Pydantic

### 2. Python Version Upgrade

**v1:**
- Python 3.8

**v2:**
- Python 3.13

### 3. Dependency Management

**v1:**
- Uses `requirements.txt` with loose version constraints
- Manual dependency specification

**v2:**
- Uses `pyproject.toml` with modern Python packaging standards
- Strict version pinning for all dependencies
- Optional dependency groups (dev, test, lint, check)
- Hatchling build system

### 4. Key Dependency Updates

| Dependency | v1 | v2 | Notes |
|------------|----|----|-------|
| Web Framework | Flask 2.3.x | FastAPI 0.115.2 | Complete framework change |
| Validation | Marshmallow 3.19.x | Pydantic 2.11.4 | Modern type validation |
| MongoDB (for JSONB marshalling) | pymongo 3.12.0 | pymongo 4.13.0 | Major version upgrade |


### 5. API Changes

**v1:**
- API prefix: `/v1`
- Accepted a mixture of formats (form, json, headers) for authentication

**v2:**
- API prefix: `/v2`
- Accepts json for authentication payload with support for SSH authentication via headers
- Changed schema to create a schedule (see openAPI docs for change in payload shape)

**NOTE**: See the API docs for the updated endpoints and schema changes

### 6. Authentication & Authorization

**v1:**
- Custom authentication decorators
- Uses subprocess to invoke openssl for cryptographic functions
- Only supports SSH keys in the RSA format

**v2:**
- FastAPI dependency injection for authentication
- Uses `cryptography` library for cryptographic functions
- Supports SSH keys in RSA and PEM formats


### 7. Models

**v1:**
- Uses `Dict`, `List`, `Optional` from typing

**v2:**
- Uses modern type annotations (`dict`, `list`, `|` union syntax)

### 8. Containerization

**v1:**
- Uses `rgaudin/uwsgi-nginx:python3.8` base image
- uWSGI + Nginx setup

**v2:**
- Uses `python:3.13-slim-bookworm` base image
- uvicorn ASGI server

### 9. Development Tools

**v2 New Features:**
- Black code formatter
- Ruff linter
- Pyright type checker
- Pre-commit hooks

## Migration Notes

### Breaking Changes

1. **API Endpoints**: All endpoints now use `/v2` prefix instead of `/v1`
2. **Request Validation**: Automatic validation with Pydantic models
3. **Schema Changes**: Modified schema definitions (See openAPI docs)

### Required Actions for Migration

1. **Update API Client**: Modify all API calls to use `/v2` prefix
2. **Update Authentication**: With the exception of SSH authentication via headers, authentication expects JSON payloads.
3. **Update Error Handling**: Adapt to new error response format

### Benefits of v2

1. **Type Safety**: Pydantic provides runtime type validation
2. **Documentation**: Automatic OpenAPI/Swagger documentation
3. **Modern Python**: Uses latest Python features and best practices
4. **Better Testing**: Comprehensive test setup with modern tools
5. **Code Quality**: Automated linting and formatting
6. **Dependency Management**: Modern packaging with strict version control

## Conclusion

Zimfarm Backend v2 represents a significant modernization that improves performance, maintainability, and developer experience. The migration from Flask to FastAPI brings modern Python web development practices while maintaining the core functionality of the Zimfarm system.
