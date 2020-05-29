FROM python:3.7

RUN apt-get update && apt-get install -y procps

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir -p /data0/webapps/assassin && \
    mkdir -p /data0/logs/assassin

WORKDIR /data0/webapps/assassin

ARG app_env

COPY requirements.txt /data0/webapps/assassin/

COPY . /data0/webapps/assassin/

RUN pip install -r requirements.txt

ENV APP_ENV $app_env

EXPOSE 8888

CMD ["python", "/data0/webapps/assassin/main.py"]