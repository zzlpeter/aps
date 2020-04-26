FROM python:3.7

RUN mkdir -p /data/app/aps && \
    mkdir -p /data/logs/app/aps && \
    mkdir -p /data/downloads

WORKDIR /data/app/aps

COPY requirements.txt /data/app/aps/

COPY . /data/app/aps/

RUN pip install -r requirements.txt

ENV APP_ENV local

CMD ["python", "/data/app/aps/main.py"]