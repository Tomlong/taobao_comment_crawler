import re
import time
import urllib
import logging
import pymongo
import requests
import threading
from threading import Thread
from bs4 import BeautifulSoup

from product_crawler_config import TMALL_URL, MONGO_URI

logger = logging.getLogger(__name__)

MONGO_CLIENT = pymongo.MongoClient(MONGO_URI)
TAOBAO_URL_DB = MONGO_CLIENT['TAOBAO_URL']

def get_category_soups():
    tmall_responce = requests.get(TMALL_URL)
    tmall_soup = BeautifulSoup(tmall_responce.text, 'html.parser')
    category_soups = tmall_soup.find(True, {'class': 'normal-nav clearfix'}).findAll('a')
    return category_soups

def get_category_url_dict(category_soups):
    category_url_dict = dict()
    for category_soup in category_soups:
        category_name = category_soup.text.strip()
        category_url = 'https:{}'.format(category_soup['href'])
        category_url_dict[category_name] = category_url
    return category_url_dict

def get_noblock_url(item_urls):
    noblock_url = None
    for url in item_urls:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        product_soups = soup.findAll(True, {'class': 'productTitle'})
        if product_soups:
            noblock_url = url
            return noblock_url
        time.sleep(3)
    return noblock_url

def _item_urls_to_db(category_name, anchors):
    item_url_collection = TAOBAO_URL_DB['item_url']

    item_search_dict = {}
    for anchor in anchors:
        try:
            href = anchor['href']
            if 'list.tmall.com/search_product.htm?' in href:
                item_search_name = anchor.text
                item_search_url = 'https:{}'.format(href)
                item_search_dict[item_search_name] = item_search_dict.get(item_search_name, [])
                item_search_dict[item_search_name].append(item_search_url)
        except:
            pass
    
    for item_name, item_urls in item_search_dict.items():
        item_url = get_noblock_url(item_urls)
        if item_url is not None:
            logger.info('crawl_item_urls >> insert {} {} to DB'.format(category_name, item_name))
            new_item_url_data = {
                'category': category_name,
                'item': item_name,
                'item_url': item_url,
                'status': 'ready',
            }
            item_url_collection.update_one(
                {
                    'category': category_name, 
                    'item': item_name
                },
                {
                    '$set': new_item_url_data
                }, upsert=True
            )

def item_urls_to_db(category_url_dict):
    item_search_dicts = []
    for category_name, category_url in category_url_dict.items():
        category_response = requests.get(category_url)
        category_soup = BeautifulSoup(category_response.text, 'html.parser')
        # 商品搜尋 href 都在 anchor 內
        anchors = category_soup.findAll('a')
        _item_urls_to_db(category_name, anchors)

        time.sleep(3)
        
    return item_search_dicts

def product_urls_to_db(job):
    category_name = job['category']
    item_name = job['item']
    item_url = job['item_url']
    item_url_id = job['_id']

    product_url_collection = TAOBAO_URL_DB['product_url']
    
    res = requests.get(item_url)
    soup = BeautifulSoup(res.text, 'html.parser')
    product_soups = soup.findAll(True, {'class': 'productTitle'})
    # parse product_url
    for product_soup in product_soups:
        product_title = product_soup.text.strip()
        product_url = 'https:{}'.format(product_soup.a['href'])
        new_product_url_data = {
            'product_title': product_title,
            'category': category_name,
            'item': item_name,
            'product_url': product_url,
            'item_url_id': item_url_id,
            'status': 'ready',
        }
        product_url_collection.update_one(
            {
                'product_title': product_title,
                'category': category_name,
                'item': item_name,
            },
            {
                '$set': new_product_url_data
            }, upsert=True
        )

def crawl_product_urls():
    item_url_collection = TAOBAO_URL_DB['item_url']

    while(True):
        job = item_url_collection.find_one({'status': 'ready'})
        if job:
            item_url_id = job['_id']
            item_url_collection.update_one(
                {'_id': item_url_id},
                {'$set': {'status': 'crawling'}}
            )
            logger.info('crawl_product_urls >> crawl item_url_id: {}'.format(item_url_id))
            product_urls_to_db(job)
            item_url_collection.update_one(
                {'_id': item_url_id},
                {'$set': {'status': 'finish'}}
            )

        else:
            logger.info('crawl_product_urls >> Waiting for new job to crawl product url')
        time.sleep(5)

def crawl_item_urls():
    # 取得 category 的 BeautifulSoup 
    logger.info('crawl_item_urls >> start get_category_soups')
    category_soups = get_category_soups()
    logger.info('crawl_item_urls >> finish get_category_soups')

    # 取得 category url dict
    logger.info('crawl_item_urls >> start get_category_url_dict')
    category_url_dict = get_category_url_dict(category_soups)
    logger.info('crawl_item_urls >> finish get_category_url_dict')

    # 找出 category 中各子類別頁面，並 insert DB
    logger.info('crawl_item_urls >> start insert item url into DB')
    item_urls_to_db(category_url_dict)
    logger.info('crawl_item_urls >> finish insert item url into DB')

def main():
    try:
        MONGO_CLIENT.server_info()
        logger.info('MongoDB connect successfully')
    except:
        logger.info('MongoDB connect failed')
        exit()

    Thread(target = crawl_item_urls).start()
    Thread(target = crawl_product_urls).start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()