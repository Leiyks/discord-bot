FROM python:3.11.7-slim

ARG TOKEN

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.7.1 \
  TOKEN=${TOKEN}

# System deps:
RUN pip install "poetry==${POETRY_VERSION}" \
  && apt update && apt install -y libopus0 ffmpeg

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --only main --no-interaction --no-ansi

# Creating folders, and files for a project:
COPY . /code

ENTRYPOINT ["poetry", "run", "bot"]
