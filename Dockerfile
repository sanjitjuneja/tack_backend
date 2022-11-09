FROM python:3.10.5-slim AS base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

FROM base AS python-deps

RUN apt-get update && apt-get -y install pipenv
RUN apt -y install libcurl4-gnutls-dev librtmp-dev

COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile

FROM base AS runtime

COPY --from=python-deps /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=python-deps /usr/local/bin/ /usr/local/bin/

WORKDIR /app/tackapp
ENV PYTHONPATH /app/tackapp:$PYTHONPATH
COPY . /app/
RUN ["chmod", "+x", "/app/docker-entrypoint.sh"]
RUN ["chmod", "+x", "/app/run_worker.sh"]
