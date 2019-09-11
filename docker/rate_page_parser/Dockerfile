FROM python:3.6

COPY requirements.txt /

RUN pip3 install --no-cache-dir -r /requirements.txt &&\
    rm requirements.txt

ENV MONGODB=0.0.0.0:2000

COPY taobao_rate_parser.py config/rate_parser_config.py /app/

COPY start_rate_parser.sh /app/

CMD ["/app/start_rate_parser.sh"]

WORKDIR /app
