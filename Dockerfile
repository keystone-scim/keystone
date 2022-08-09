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

RUN set -x && \
    apk add --no-cache curl gcc libffi-dev libressl-dev musl-dev clang lld rust cargo

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-dev

# ------------------------
# Runtime stage:
# ------------------------
FROM base as runtime

RUN set -x && \
    apk add --no-cache libressl-dev rust

# Avoid running the web service as a root user:
RUN addgroup -S apigroup && \
    adduser -S apiuser -G apigroup
USER apiuser

WORKDIR $PYSETUP_PATH
COPY --from=build $POETRY_HOME $POETRY_HOME
COPY --from=build $PYSETUP_PATH $PYSETUP_PATH

COPY ./keystone /$PYSETUP_PATH/keystone

EXPOSE 5001
CMD ["poetry", "run", "keystone"]
