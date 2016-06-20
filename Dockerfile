FROM python:2.7

MAINTAINER Sinfonier Project

RUN apt-get update && apt-get -y upgrade && apt-get install -y libffi-dev

RUN mkdir /app /logs
COPY ./requirements.txt /app

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app

ENV SINFONIER_LOG "/logs/sinfonier-log.log"

RUN cd /app && python setup.py install

EXPOSE 8899

CMD "sinfonier-api"
