FROM python:3.10.5-slim

WORKDIR /app/tackapp
RUN apt-get update && apt-get -y install pipenv
COPY Pipfile.lock /app/
COPY Pipfile /app/
RUN pipenv install --system --deploy --ignore-pipfile
COPY . /app/
RUN ["chmod", "+x", "/app/docker-entrypoint.sh"]