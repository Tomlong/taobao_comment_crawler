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
from selenium.webdriver import ActionChains
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
            swipe_down(driver, 1.2)
            driver.find_element_by_css_selector('#J_Reviews > div > div.rate-page > div > a:last-child').click()
            time.sleep(5)
        except:
            # 找不到下一頁
            break

def swipe_down(driver, second):
    for i in range(int(second/0.1)):
        js = "window.scrollBy(0,250)"
        driver.execute_script(js)
        time.sleep(0.2)


def crawl_rate_page(driver, job):
    timeout = 20
    product_url = job['product_url']
    try:
        driver.get(product_url)
        # 判斷是否有評論的Tab
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.ID, "J_TabBarBox")))
        time.sleep(2)
    except TimeoutException:
        logging.info('未找到評論Tab')
        return

    try:
        # 頁面scrol，看到評論Tab，模擬人的動作
        swipe_down(driver, 0.3)
    
    except WebDriverException:
        logging.info('頁面Scroll出問題')
        return

    try:
        driver.find_element_by_xpath('//*[@id="J_TabBar"]/li[2]').click()
        time.sleep(5)
        logging.info('點擊累計評論Tab成功')
    except:
        logging.info('沒有累計評論的Tab')
        return
    
    
    try:
        iframe_list = driver.find_elements_by_tag_name('iframe')
        # 出現滑動驗證
        if len(iframe_list) == 3:
            driver.switch_to_frame(iframe_list[-1])
        WebDriverWait(driver, 10, 0.5).until(EC.presence_of_element_located((By.ID, "nc_1_n1z"))) #等待滑动拖动控件出现
        swipe_button = driver.find_element_by_id('nc_1_n1z') #获取滑动拖动控件

        #模拟拽托
        action = ActionChains(driver) # 实例化一个action对象
        action.click_and_hold(swipe_button).perform() # perform()用来执行ActionChains中存储的行为
        action.reset_actions()
        action.move_by_offset(580, 0).perform() # 移动滑块

    except Exception as e:
        print ('get button failed: ', e)
    
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
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation']) 
    driver = webdriver.Chrome('./chromedriver', options = chrome_options)

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
    time.sleep(5)

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