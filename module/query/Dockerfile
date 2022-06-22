FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y \
            procps

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

RUN mkdir -p /scripts
COPY ./scripts /scripts

WORKDIR /
ENV PATH "$PATH:/scripts"
