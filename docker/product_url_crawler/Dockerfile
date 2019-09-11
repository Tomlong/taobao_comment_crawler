FROM python:3.6

COPY requirements.txt /

RUN pip3 install --no-cache-dir -r /requirements.txt &&\
    rm requirements.txt

ENV MONGODB=0.0.0.0:2000

COPY taobao_product_crawler.py config/product_crawler_config.py /app/

COPY start_product_crawler.sh /app/

CMD ["/app/start_product_crawler.sh"]

WORKDIR /app
