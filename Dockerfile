# ------------------------
# Python base stage:
# ------------------------
FROM python:3.9.13-alpine3.16 as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYSETUP_PATH=/opt/pysetup \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_IN_PROJECT=true

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# ------------------------
# Environment build stage:
# ------------------------
FROM base as build

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.1.13

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

RUN set -x && \
    apk add --no-cache --virtual .build-deps \
      postgresql-dev \
      build-base \
      gcc \
      curl \
      python3-dev \
      libffi-dev \
      libressl-dev \
      musl-dev \
      lld \
      rust \
      cargo && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    poetry install --no-dev && \
    apk del --no-cache .build-deps

# ------------------------
# Runtime stage:
# ------------------------
FROM base as runtime

RUN set -x && \
    apk add --no-cache rust libpq

RUN addgroup -S apigroup && \
    adduser -S apiuser -G apigroup
USER apiuser

WORKDIR $PYSETUP_PATH
COPY --from=build $POETRY_HOME $POETRY_HOME
COPY --from=build $PYSETUP_PATH $PYSETUP_PATH

COPY ./keystone /$PYSETUP_PATH/keystone

EXPOSE 5001
CMD ["poetry", "run", "keystone"]
