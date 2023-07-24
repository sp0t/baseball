from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver_path = ChromeDriverManager().install()
driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)

url = f"https://fightodds.io/recent-mma-events"

driver.get(url)
exercise1_card = driver.find_element(By.CLASS_NAME, '.MuiPaper-root.MuiCard-root.jss1906.MuiPaper-elevation1 MuiPaper-rounded')
print(exercise1_card)
driver.quit()

print("success!")