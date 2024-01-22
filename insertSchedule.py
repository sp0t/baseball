from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime, timedelta

# Define the start and end dates
start_date = datetime.strptime("2024/02/23", "%Y/%m/%d")
end_date = datetime.strptime("2024/12/30", "%Y/%m/%d")

# Initialize the current date to the start date
current_date = start_date

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('/home/.wdm/drivers/chromedriver',chrome_options=chrome_options)
# driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Iterate from the start date to the end date
# while current_date <= end_date:
#     print(current_date.strftime("%Y-%m-%d"))
    # url = f"https://www.mlb.com/schedule/{current_date.strftime("%Y-%m-%d")}"
    # driver.get(url)
    # wait = WebDriverWait(driver, 10)
    # get_url = driver.current_url
    # wait.until(EC.url_to_be(url))

    # page_source = driver.page_source
    # soup = BeautifulSoup(page_source)

    # data_container = soup.find('div', attrs={"id": "gridWrapper"})
    # game_container = data_container.find('div', attrs={"data-mlb-test": "individualGamesContainer"})
    # if game_container == None:
    #     break
    # current_date += timedelta(days=1)



url = f"https://www.mlb.com/schedule/2024-02-24"
driver.get(url)

wait = WebDriverWait(driver, 10)
get_url = driver.current_url
wait.until(EC.url_to_be(url))

page_source = driver.page_source
soup = BeautifulSoup(page_source)

data_container = soup.find('div', attrs={"id": "gridWrapper"})
game_container = data_container.find('div', attrs={"data-mlb-test": "individualGamesContainer"})

if game_container == None:
    print('no data')
else:
    empty_container = game_container.find('div', attrs={"class": "ScheduleCollectionGridstyle__EmptyDateLabel-sc-c0iua4-7 cXJoFI"})
    if empty_container is None:
        teams = game_container.findAll('div', attrs={"data-mlb-test": "individualGameContainerDesktop"})
        for team in teams:    
            teams_container = team.find('div', attrs={"data-mlb-test": "scoreOrState"})
            away_container = teams_container.find('div', attrs={"class": "TeamMatchupLayerstyle__AwayWrapper-sc-ouprud-1 dmSctg"})
            away_title_container = away_container.find('div', attrs={"class": "TeamWrappersstyle__MobileTeamWrapper-sc-uqs6qh-1 IESfj"})
            away = away_title_container.text
            home_container = teams_container.find('div', attrs={"class": "TeamMatchupLayerstyle__HomeWrapper-sc-ouprud-2 hHOoUi"})
            home_title_container = home_container.find('div', attrs={"class": "TeamWrappersstyle__MobileTeamWrapper-sc-uqs6qh-1 IESfj"})
            home = home_title_container.text
            print(away)
            print(home)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
    else:
        print("no team")

driver.quit()

print("success!")

