FROM python:3.9.5-slim as builder

WORKDIR /app
RUN pip3 install poetry

ENV POETRY_VIRTUALENVS_CREATE false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root --no-dev

FROM python:3.9.5-slim

WORKDIR /app
VOLUME /app/instance

COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY . .

EXPOSE 3000
CMD flask database create \
    && flask db upgrade \
    && gunicorn --bind 0.0.0.0:3000 wsgi:app