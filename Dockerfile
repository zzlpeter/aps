FROM python:3.7

RUN mkdir -p /data/app/assassin && \
    mkdir -p /data/logs/app/assassin && \
    mkdir -p /data/downloads

WORKDIR /data/app/assassin

COPY requirements.txt /data/app/assassin/

COPY . /data/app/assassin/

RUN pip install -r requirements.txt

ENV APP_ENV local

EXPOSE 8888

CMD ["sh", "/data/app/assassin/start.sh"]