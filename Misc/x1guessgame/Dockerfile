FROM python:3.10-slim-bullseye

WORKDIR /app

COPY ./app/ /app

COPY ./docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod -R 555 /app

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list
RUN apt-get update -y && apt-get install -y curl git
RUN python3 -m pip install -i https://mirror.nju.edu.cn/pypi/web/simple/ -r requirements.txt

ENV PATH="$PATH:/root/.foundry/bin"
RUN curl -L https://foundry.paradigm.xyz | bash

RUN foundryup

EXPOSE 5000

# 指定容器入口点
ENTRYPOINT ["/bin/bash","/docker-entrypoint.sh"]