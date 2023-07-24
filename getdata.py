from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
from selenium.webdriver.common.by import By

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver_path = ChromeDriverManager().install()
driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)

url = f"https://fightodds.io/recent-mma-events"

driver.get(url)
# myDiv = driver.find_element(By.CLASS_NAME, '.MuiGrid-root.MuiGrid-container')
# print(myDiv.get_attribute("outerHTML"))
wait = WebDriverWait(driver, 10)
get_url = driver.current_url
wait.until(EC.url_to_be(url))

page_source = driver.page_source
soup = BeautifulSoup(page_source)
print(soup)
driver.quit()

print("success!")