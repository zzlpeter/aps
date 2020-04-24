FROM python:3.7

RUN mkdir -p /data/app/data && \
    mkdir -p /data/logs/app && \
    mkdir -p /data/downloads

WORKDIR /data/app/data

COPY requirements.txt /data/app/data/

COPY . /data/app/data/

RUN pip install -r requirements.txt

ENV APP_ENV online

EXPOSE 80

CMD ["python", "/data/app/data/main.py"]