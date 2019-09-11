import os
import time
import gridfs
import logging
import pymongo
from bs4 import BeautifulSoup

from rate_parser_config import SPECIAL_CHARS, MONGO_URI

logger = logging.getLogger(__name__)


MONGO_CLIENT = pymongo.MongoClient(MONGO_URI)
TAOBAO_RATE_PAGE_DB = MONGO_CLIENT['TAOBAO_RATE_PAGE']
FS = gridfs.GridFS(TAOBAO_RATE_PAGE_DB)


def process_comment(string):
    for char in SPECIAL_CHARS:
        string = string.replace(char, '')
    string = string.strip()

    return string

def parse_comment(comment_datas, job):

    rate_page_id = job['_id']
    product_title = job['product_title']
    category = job['category']
    item = job['item']
    
    parse_datas = []
    for comment_data in comment_datas: 
        goodstype_list = [] 
        username_list = []
        parse_data = {
            'rate_page_id': rate_page_id,
            'product_title': product_title,
            'category': category,
            'item': item,
            'comment1': '',
            'comment2': '', 
            'goodstype': goodstype_list, 
            'username': username_list
        }
        try:
            comment = comment_data.find('div', class_ = "tm-rate-premiere").find('div', class_ = "tm-rate-content")
            comment_text = comment.text
            comment_1 = process_comment(comment_text)
            parse_data['comment1'] = comment_1
        except:
            pass

        # 若第一個 comment1 格式沒有 parse 出來，則 try 下一個格式
        if parse_data['comment1'] == '':
            try:
                comment = comment_data.find('div', class_ = "tm-rate-content").find('div', class_ = "tm-rate-fulltxt")
                comment_text = comment.text
                comment_1 = process_comment(comment_text)
                parse_data['comment1'] = comment_1
            except:
                pass

        try:
            comment = comment_data.find('div', class_ = "tm-rate-append").find('div', class_ = "tm-rate-content")
            comment_text = comment.text
            comment_2 = process_comment(comment_text)
            parse_data['comment2'] = comment_2
        except:
            pass

        goodstypes = comment_data.find('div',class_="rate-sku").find_all('p')
        for goodstype in goodstypes:
            goodstype_list.append(goodstype.attrs['title'])
        
        usernames = comment_data.find_all('div',class_="rate-user-info")
        for username in usernames:
            username_list.append(username.text.strip())
        
        parse_data['goodstype'] = ','.join(goodstype_list)
        parse_data['username'] = ','.join(username_list)

        parse_datas.append(parse_data)
    return parse_datas

def parse_comment_to_db(job):
    rate_comment_collection = TAOBAO_RATE_PAGE_DB['rate_comment']

    dataset_id = job['id']
    stream = FS.get(dataset_id)
    html = stream.read()
    soup = BeautifulSoup(html, 'html.parser')
    comment = soup.find("div",class_="rate-grid")
    comment_datas = comment.find_all("tr")

    parse_datas = parse_comment(comment_datas, job)

    # insert data to DB
    if len(parse_datas) != 0:
        rate_comment_collection.insert_many(parse_datas)

def main():
    try:
        MONGO_CLIENT.server_info()
        logging.info('MongoDB connect successfully')
    except:
        logging.info('MongoDB connect failed')
        exit()

    rate_page_collection = TAOBAO_RATE_PAGE_DB['rate_page']

    while(True):
        job = rate_page_collection.find_one_and_update(
            {'status': 'ready'}, 
            {'$set': {'status': 'parsing'}}
        )
        if job:
            parse_comment_to_db(job)
            job_id = job['_id']
            logger.info(f"Job {job_id} finish")
            rate_page_collection.find_one_and_update(
                {'_id': job_id},
                {'$set': {'status': 'finish'}}
            )
        else:
            logging.info('Waiting for new page to parse')
            time.sleep(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()