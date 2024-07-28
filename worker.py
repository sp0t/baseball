from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = f"https://baseballsavant.mlb.com/gamefeed?date=6/21/2024&gamePk=744841&chartType=pitch&leg[%E2%80%A6]Filter=&resultFilter=&hf=winProbability&sportId=1&liveAb="
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

driver.close()