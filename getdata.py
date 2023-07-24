from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.headless = True

DRIVER_PATH = '/path/to/chromedriver'
driver = webdriver.Chrome(executable_path=DRIVER_PATH)
driver.get('https://google.com')

print(driver.page_source)
driver.quit()