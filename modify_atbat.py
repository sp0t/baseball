from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
import pandas as pd

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome('/home/.wdm/drivers/chromedriver',chrome_options=chrome_options)
# driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# db_string = "postgresql://postgres:123@localhost:5432/testdb"
# db = create_engine(db_string)

db = create_engine('postgresql://postgres:123@ec2-18-180-226-162.ap-northeast-1.compute.amazonaws.com:5432/betmlb', 
                                connect_args = {'connect_timeout': 10}, 
                                echo=False, pool_size=20, max_overflow=0)

data = pd.read_sql(f"SELECT * FROM game_table WHERE away_score = '0' AND home_score = '0' ORDER BY game_date;", con = db).to_dict('records')

for el in data:
    team1 = pd.read_sql(f"SELECT club_name FROM team_table WHERE team_abbr = '{el['away_team']}'", con = db).to_dict('records')
    team2 = pd.read_sql(f"SELECT club_name FROM team_table WHERE team_abbr = '{el['home_team']}'", con = db).to_dict('records')

    if team1 == []:
        if el['away_team'] == 'ARI':
            away_team = 'd-backs'
        else:
            continue
    else:
        away_teams = team1[0]['club_name'].lower().split(' ')

        if len(away_teams) == 2:
            away_team = f'{away_teams[0]}-{away_teams[1]}'
        else:
            away_team = away_teams[0]

    if team2 == []:
        if el['home_team'] == 'ARI':
            home_team = 'd-backs'
        else:
            continue
    else:
        home_teams = team2[0]['club_name'].lower().split(' ')
        if len(home_teams) == 2:
            home_team = f'{home_teams[0]}-{home_teams[1]}'
        else:
            home_team = home_teams[0]
    

    url = f"https://www.mlb.com/gameday/{away_team}-vs-{home_team}/{el['game_date']}/{el['game_id']}/final/box"
    print(url)

    driver.get(url)

    wait = WebDriverWait(driver, 10)
    get_url = driver.current_url
    wait.until(EC.url_to_be(url))

    page_source = driver.page_source
    soup = BeautifulSoup(page_source)
    
    atbats_tables = soup.findAll('table', attrs={"class":"tablestyle__StyledTable-sc-wsl6eq-0 kfhorh BoxscoreTeamTablestyle__TeamTable-sc-15fvlso-1 dgwGLd batters"})
    table_score = soup.find('table', attrs={"class":"tablestyle__StyledTable-sc-wsl6eq-0 bqIWWu"})
    
    if table_score == None:
        continue
    scores = table_score.find('tbody').find_all('tr')
    score1 = scores[0].find('td', attrs = {'data-col':'0'}).find('div').text
    score2 = scores[1].find('td', attrs = {'data-col':'0'}).find('div').text

    db.execute(f"UPDATE game_table SET away_score='{score1}', home_score = '{score2}' WHERE game_id='{el['game_id']}';")

    for i in range(len(atbats_tables)):
        team_name = atbats_tables[i].find('thead').find('tr').find('th', attrs = {'data-col':'0'})
        tbody = atbats_tables[i].find('tbody').find_all('tr')


        for i in range(9):
            url = tbody[i].find('td', attrs = {'data-col':'0'}).find('div').find('span').find('a').get('href')
            p_attabt = tbody[i].find('td', attrs = {'data-col':'1'}).find('span').text
            p_id = url.split("/")[-1]
            db.execute(f"UPDATE batter_table SET atbats='{p_attabt}' WHERE game_id='{el['game_id']}' AND playerid='{p_id}';")
            
driver.quit()

print("success!")