from selenium import webdriver
import chromedriver_autoinstaller

chromedriver_autoinstaller.install()

driver = webdriver.Chrome()
driver.get("http://www.python.org")

driver.quit()