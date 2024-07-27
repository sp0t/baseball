from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
import pandas as pd

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# driver = webdriver.Chrome('/usr/bin/chromedriver',chrome_options=chrome_options)
driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()))

url = f"https://fightodds.io/recent-mma-events"
print('###################################################')
print('##                                               ')
print(f'##   {url}                                      ')
print('##                                               ')
print('###################################################')
driver.get(url)

wait = WebDriverWait(driver, 10)
get_url = driver.current_url
wait.until(EC.url_to_be(url))

page_source = driver.page_source
soup = BeautifulSoup(page_source)
print(soup)