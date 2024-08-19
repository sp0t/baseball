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
from datetime import datetime
import time

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
# gameData = pd.read_sql(f"SELECT * FROM game_table WHERE game_date = (SELECT MAX(game_date) FROM game_table);", con = engine).to_dict('records')
gameData = pd.read_sql(f"SELECT * FROM game_table WHERE TO_DATE(game_date, 'YYYY/MM/DD') >= DATE '2024-08-16' ORDER BY game_date;", con = engine).to_dict('records')

for game in gameData:
    date_obj = datetime.strptime(game['game_date'], "%Y/%m/%d")
    formatted_date = date_obj.strftime("%m/%d/%Y")

    try:
        url = f"https://baseballsavant.mlb.com/gamefeed?date={formatted_date}&gamePk={game['game_id']}&chartType=pitch&leg[…]Filter=&resultFilter=&hf=winProbability&sportId=1&liveAb="
        print('##                                               ')
        print(f'##   {url}                                      ')
        print('###################################################')
        driver.get(url)
        divId = f"tableWinProbability_{game['game_id']}"

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, divId)))
        # get_url = driver.current_url
        # wait.until(EC.url_to_be(url))

        time.sleep(5)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        # soup = BeautifulSoup(page_source)
        table_data = soup.find('div', id=divId)
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
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '1', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T3' and preGame == 'B2'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '2', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T4' and preGame == 'B3'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '3', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T5' and preGame == 'B4'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '4', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T6' and preGame == 'B5'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '5', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T7' and preGame == 'B6'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '6', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T8' and preGame == 'B7'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '7', '{awayWin}', '{homeWin}');"))
                    if(linespan.get_text() == 'T9' and preGame == 'B8'):
                        engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '8', '{awayWin}', '{homeWin}');"))

                    preGame = linespan.get_text()
                else:
                    print("No span found in this td.")
                awayWin = tmpawayWin
                homeWin = tmphomeWin
            
            engine.execute((f"INSERT INTO win_prob(game_id, game_date, away_team, home_team, line, away_wp, home_wp) VALUES('{game['game_id']}', '{game['game_date']}', '{game['away_team']}', '{game['home_team']}', '9', '{awayWin}', '{homeWin}');"))

        else:
            engine.execute((f"INSERT INTO error_game(game_id, game_date) VALUES('{game['game_id']}', '{game['game_date']}');"))
    
        # driver.close()

    except Exception as e:
        print(f"An error occurred: {e}")
