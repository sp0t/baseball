from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# Automatically download and use the correct version of ChromeDriver
driver = webdriver.Chrome(ChromeDriverManager().install())

# Open a website
driver.get('http://www.google.com')

# Close the browser
driver.quit()
