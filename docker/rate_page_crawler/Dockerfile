FROM ubuntu:16.04

########################################################### ENVIRONMENT: base ################################################
USER root

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get install -y build-essential python3.6 python3.6-dev python3-pip python3.6-venv python-pymongo
RUN python3.6 -m pip install pip --upgrade

########################################################### Application needed: ################################################
# ------- Install additionnal libraries with "apt-get -y"
RUN apt-get install -y libsm6 libxext6 libglib2.0-0 libxrender-dev
# ------- Or annd needed libraries into "requirements.txt" file and use it:

COPY requirements.txt /

RUN python3.6 -m pip install -r requirements.txt &&\
    rm requirements.txt

ENV MONGODB=0.0.0.0:2000

RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget

COPY taobao_rate_crawler.py config/rate_crawler_config.py utils.py /app/

COPY start_rate_crawler.sh /app/

COPY connection.py launcher.py /usr/local/lib/python3.6/dist-packages/pyppeteer/

CMD ["/app/start_rate_crawler.sh"]

WORKDIR /app