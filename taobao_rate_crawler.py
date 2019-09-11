import re
import time
import urllib
import gridfs
import pymongo
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from rate_crawler_config import PROXIES, LOGIN_HEADERS, LOGIN_URL, POST_DATA, MONGO_URI, VST_URL

logger = logging.getLogger(__name__)

MAX_PAGE = 50
session = requests.Session()
session.proxies = PROXIES

MONGO_CLIENT = pymongo.MongoClient(MONGO_URI)
TAOBAO_URL_DB = MONGO_CLIENT['TAOBAO_URL']
TAOBAO_RATE_PAGE_DB = MONGO_CLIENT['TAOBAO_RATE_PAGE']
FS = gridfs.GridFS(TAOBAO_RATE_PAGE_DB)


def get_st_code():
    # 取得 st_code 的請取 url 
    opener = urllib.request.build_opener()
    request = urllib.request.Request(LOGIN_URL, POST_DATA, LOGIN_HEADERS)
    response = opener.open(request)
    content = response.read().decode('gbk')
    pattern = re.compile('<script src=\"(.*)\"><\/script>')
    match = pattern.search(content)
    # 取得 st_code 請取 url
    st_url = match.group(1)
    # request st_code
    st_response = session.get(st_url)
    # parse st_code
    st_match = re.search(r'"data":{"st":"(.*?)"}', st_response.text)
    st_code = st_match.group(1)

    return st_code


def _crawl_rate_page(driver, job):
    rate_page_db = TAOBAO_RATE_PAGE_DB['rate_page']
    for page in range(MAX_PAGE):
        logging.info('crawling page{}'.format(str(page+1)))
        html = driver.page_source.encode('utf-8')
        information = {
            'product_title': job['product_title'],
            'category': job['category'],
            'item': job['item'],
            'product_url': job['product_url'],
            'page': page,
        }

        if not FS.find_one(information):
            obj_id = FS.put(html, **information)
            rate_page_db.insert({
                'id': obj_id,
                'product_title': job['product_title'],
                'category': job['category'],
                'item': job['item'],
                'product_url': job['product_url'],
                'page': page,
                'status': 'ready',
            })

        try:
            driver.find_element_by_css_selector('#J_Reviews > div > div.rate-page > div > a:last-child').click()
            time.sleep(10)
        except:
            # 找不到下一頁
            break

def crawl_rate_page(driver, job):
    timeout = 20
    product_url = job['product_url']
    try:
        driver.get(product_url)
        # 判斷是否有評論的Tab
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, "J_TabBarBox")))
        time.sleep(5)
    except TimeoutException:
        logging.info('未找到評論Tab')
        return

    try:
        # 頁面scroll至800位置，看到評論Tab，模擬人的動作
        js = "window.scrollTo(0,800)"
        driver.execute_script(js)
        time.sleep(10)
    except WebDriverException:
        logging.info('頁面Scroll出問題')
        return

    try:
        driver.find_element_by_xpath('//*[@id="J_TabBar"]/li[2]').click()
        time.sleep(10)
        logging.info('點擊累計評論Tab成功')
    except:
        logging.info('沒有累計評論的Tab')
        return
    
    try:
        driver.find_element_by_xpath('//*[@id="J_Reviews"]/div/div[@class="rate-grid"]')
        _crawl_rate_page(driver, job)
    except Exception as e:
        logging.info(e)
        logging.info('累計評論沒載入成功')
        return


def login():
    # 透過取得 st_code 登入 taobao
    st_code = get_st_code()
    login_st_url = VST_URL.format(st_code)
    # driver setup
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(chrome_options=chrome_options)

    driver.implicitly_wait(10)
    driver.get(login_st_url)

    return driver

def main():
    try:
        MONGO_CLIENT.server_info()
        logging.info('MongoDB connect successfully')
    except:
        logging.info('MongoDB connect failed')
        exit()
    
    # 登入
    driver = login()
    logging.info('login success')

    # 爬取 rate page
    product_urls_db = TAOBAO_URL_DB['product_url']
    while(True):
        job = product_urls_db.find_one_and_update({'status': 'ready'}, {'$set': {'status': 'crawling'}})
        if job:
            logging.info('crawling product title:{}'.format(job['product_title']))
            crawl_rate_page(driver, job)
            product_urls_db.find_one_and_update({'_id': job['_id']}, {'$set':{'status': 'finish'}})
            logging.info('crawling finish')

        else:
            logging.info('Waiting for new product url')
    
        time.sleep(10)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()