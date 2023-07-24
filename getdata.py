import platform       
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

options = Options()
# a few usefull options
options.add_argument("--disable-infobars")
options.add_argument("start-maximized")
options.add_argument("--disable-extensions")
options.add_argument("--headless") # if you want it headless

driver_path = ChromeDriverManager().install()

service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

url = "https://fightodds.io/recent-mma-events"

wait = WebDriverWait(driver, 10)

driver.get(url)


get_url = driver.current_url
wait.until(EC.url_to_be(url))


if get_url == url:
   page_source = driver.page_source
   print(page_source)

driver.quit()