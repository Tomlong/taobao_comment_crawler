FROM python:3.6

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99


COPY requirements.txt /

RUN pip3 install --no-cache-dir -r /requirements.txt &&\
    rm requirements.txt

ENV MONGODB=0.0.0.0:2000

COPY taobao_rate_crawler.py config/rate_crawler_config.py /app/

COPY start_rate_crawler.sh /app/

CMD ["/app/start_rate_crawler.sh"]

WORKDIR /app