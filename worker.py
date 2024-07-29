from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
import pandas as pd

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
gameData = pd.read_sql(f"SELECT * FROM game_table ORDER BY game_date;", con = engine).to_dict('records')

for game in gameData:
    print(game)

try:
    url = f"https://baseballsavant.mlb.com/gamefeed?date=7/27/2024&gamePk=744908&chartType=pitch&leg[…]Filter=&resultFilter=&hf=winProbability&sportId=1&liveAb="
    print('##                                               ')
    print(f'##   {url}                                      ')
    print('###################################################')
    driver.get(url)

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, 'tableWinProbability_744908')))
    # get_url = driver.current_url
    # wait.until(EC.url_to_be(url))

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    table_data = soup.find('div', id='tableWinProbability_744908')
    tbody = table_data.find('tbody')

    if tbody:
        awayWin = 0
        homeWin = 0
        preGame = 'T1'

        for tr in reversed(tbody.find_all('tr')):
            tds = tr.find_all('td')
            # for td in tds:
            linespan = tds[1].find('span')
            if linespan:
                tmpawayWin = 0
                tmphomeWin = 0
                
                awayspan = tds[6].find('span')
                if awayspan:
                    tmpawayWin = awayspan.get_text()
                else:
                    tmpawayWin = awayspan.get_text()
                
                homespan = tds[5].find('span')

                if homespan:
                    tmphomeWin = homespan.get_text()
                else:
                    tmphomeWin = homespan.get_text()
                if(linespan.get_text() == 'T2' and preGame == 'B1'):
                    print('B1', homeWin, '-', awayWin) 
                if(linespan.get_text() == 'T3' and preGame == 'B2'):
                    print('B2', homeWin, '-', awayWin)
                if(linespan.get_text() == 'T4' and preGame == 'B3'):
                    print('B3', homeWin, '-', awayWin)
                if(linespan.get_text() == 'T5' and preGame == 'B4'):
                    print('B4', homeWin, '-', awayWin)
                if(linespan.get_text() == 'T6' and preGame == 'B5'):
                    print('B5', homeWin, '-', awayWin)
                if(linespan.get_text() == 'T7' and preGame == 'B6'):
                    print('B6', homeWin, '-', awayWin)
                if(linespan.get_text() == 'T8' and preGame == 'B7'):
                    print('B7', homeWin, '-', awayWin)
                if(linespan.get_text() == 'T9' and preGame == 'B8'):
                    print('B8', homeWin, '-', awayWin)

                preGame = linespan.get_text()
            else:
                print("No span found in this td.")
            awayWin = tmpawayWin
            homeWin = tmphomeWin
        
        print('B9', homeWin, '-', awayWin) 

    else:
        print("No tbody found in the HTML.")
    

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    driver.close()