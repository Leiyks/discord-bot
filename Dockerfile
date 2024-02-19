FROM python:3.11.7-slim

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.7.1

# System deps:
RUN apt update -y \
  && apt upgrade -y \
  && apt install -y libopus0 ffmpeg

RUN pip install --upgrade pip \
  && pip install "poetry==${POETRY_VERSION}"

WORKDIR /code
COPY . /code

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --only main --no-interaction --no-ansi

ENTRYPOINT ["poetry", "run", "bot"]
