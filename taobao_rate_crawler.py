import re
import time
import urllib
import gridfs
import asyncio
import pymongo
import logging
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch

from utils import slide_list
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


async def _crawl_rate_page(page, job):
    rate_page_db = TAOBAO_RATE_PAGE_DB['rate_page']
    for page_num in range(MAX_PAGE):
        logging.info('crawling page{}'.format(str(page_num+1)))
        page_content = await page.content()
        html = page_content.encode('utf-8')
        information = {
            'product_title': job['product_title'],
            'category': job['category'],
            'item': job['item'],
            'product_url': job['product_url'],
            'page': page_num,
        }

        if not FS.find_one(information):
            obj_id = FS.put(html, **information)
            rate_page_db.insert({
                'id': obj_id,
                'product_title': job['product_title'],
                'category': job['category'],
                'item': job['item'],
                'product_url': job['product_url'],
                'page': page_num,
                'status': 'ready',
            })

        try:
            next_page = await page.J('#J_Reviews > div > div.rate-page > div > a:last-child')
            await next_page.click()
            await asyncio.sleep(2)
        except:
            logger.info('找不到下一頁')
            break

async def check_pass_evaluate(page):

    if len(page.frames) == 4:
        logger.info('出現驗證')
        frame_list = page.frames
        evaluate_frame = frame_list[3]
        await evaluate_frame.Jeval('#nocaptcha', 'node => node.style')
        await evaluate_frame.hover('#nc_1_n1z')
        
        logger.info('開始破解驗證')
        await page.mouse.down()
        slides = slide_list(260)
        logger.info(f'{slides}')
        x = page.mouse._x
        for distance in slides:
            x += distance
            await page.mouse.move(x, 0, )
        await page.mouse.up()
        
        logger.info('完成破解驗證')
        await asyncio.sleep(5)
        logger.info(f'{page.frames}')
        await page.reload()
        await asyncio.sleep(5)
        logger.info('重新讀取')
        await click_rate(page)
    else:
        logger.info('未出現驗證')

async def click_rate(page):
    timeout = 10
    try:
        await asyncio.sleep(5)
        # 按累計評論
        comment_button = await page.Jx('//*[@id="J_TabBar"]/li[2]')
        logging.info(f'按累計評論{comment_button}')
        await comment_button[0].click()
        await asyncio.sleep(3)
    except Exception as e:
        logging.info(f'按累計評論Tab失敗{e}')
        return

async def crawl_rate_page(page, job):
    timeout = 10
    product_url = job['product_url']
    await page.goto(product_url)
    await click_rate(page)
    
    # 等待是否有驗證frame
    await asyncio.sleep(5)
    try:
        await check_pass_evaluate(page)

    except Exception as e:
        print ('驗證失敗 ', e)
    
    try:
        rate_part = await page.Jx('//*[@id="J_Reviews"]/div/div[@class="rate-grid"]')
        if len(rate_part) == 1:
            await _crawl_rate_page(page, job)
    except Exception as e:
        logging.info(e)
        logging.info('累計評論沒載入成功')
        return


async def login():
    # 透過取得 st_code 登入 taobao
    st_code = get_st_code()
    login_st_url = VST_URL.format(st_code)

    # driver setup
    launch_kwargs = {
        "headless": True,
        'args': [
            '--no-sandbox',
        ],
    }

    browser = await launch(launch_kwargs)
    page = await browser.newPage()
    await page.goto(login_st_url)

    '''chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation']) 
    driver = webdriver.Chrome(options = chrome_options)

    driver.implicitly_wait(10)
    driver.get(login_st_url)'''

    return page


async def start():
     # 登入
    page = await login()
    logging.info('login success')
    await asyncio.sleep(5)

    # 爬取 rate page
    product_urls_db = TAOBAO_URL_DB['product_url']


    while(True):
        job = product_urls_db.find_one_and_update({'status': 'ready'}, {'$set': {'status': 'crawling'}})
        if job:
            logging.info('crawling product title:{}'.format(job['product_title']))
            await crawl_rate_page(page, job)
            product_urls_db.find_one_and_update({'_id': job['_id']}, {'$set':{'status': 'finish'}})
            logging.info('crawling finish')

        else:
            logging.info('Waiting for new product url')
    
        await asyncio.sleep(10)

def main():
    try:
        MONGO_CLIENT.server_info()
        logging.info('MongoDB connect successfully')
    except:
        logging.info('MongoDB connect failed')
        exit()
    
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(start())
    loop.run_until_complete(task)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()