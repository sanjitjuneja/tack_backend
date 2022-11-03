FROM python:3.10.5-slim AS base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

FROM base AS python-deps

RUN pip install --upgrade pip
RUN pip install pipenv

COPY Pipfile Pipfile.lock ./
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM base AS runtime

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
WORKDIR /app/tackapp
COPY . /app/
RUN ["chmod", "+x", "/app/docker-entrypoint.sh"]
RUN ["chmod", "+x", "/app/run_worker.sh"]
