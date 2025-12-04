# =======================================
# Stage 1: init
# =======================================
FROM ghcr.io/astral-sh/uv:0.9.8-python3.13-bookworm AS init

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1
ENV UV_NO_DEV=1

# Copy local context to `/app` inside container (see .dockerignore)
COPY ./comprl .
COPY ./comprl-hockey-game /hockey

RUN apt-get update && apt-get install -y swig

# Install comprl server
RUN uv sync --locked --extra monitor
RUN uv pip install -r /hockey/requirements.txt


# =======================================
# Stage 2: copy artifacts into slim image
# =======================================
FROM python:3.13-slim

WORKDIR /app
RUN adduser --disabled-password --home /app comprl
COPY --chown=comprl --from=init /app /app
COPY --chown=comprl --from=init /hockey /hockey

USER comprl
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1

# 'exec' is important here so that signals are properly propagated to the comprl-server
# process (needed for config reloading)
CMD exec comprl-server --config "${COMPRL_CONFIG_PATH}"
