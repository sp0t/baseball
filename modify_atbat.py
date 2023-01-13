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

data = pd.read_sql(f"SELECT a.num, b.* FROM (SELECT * FROM game_table) b LEFT JOIN (SELECT game_id, COUNT(*)num FROM batter_table WHERE avg = '0.0' AND obp = '0.0' AND ops = '0.0' AND slg = '0.0' GROUP BY game_id)a ON a.game_id = b.game_id WHERE a.num = '18' ORDER BY b.game_date;", con = db).to_dict('records')
print(data)

for el in data:
    if el['game_date'].find('2022') == -1:
        continue
    team1 = pd.read_sql(f"SELECT club_name FROM team_table WHERE team_abbr = '{el['away_team']}'", con = db).to_dict('r')
    team2 = pd.read_sql(f"SELECT club_name FROM team_table WHERE team_abbr = '{el['home_team']}'", con = db).to_dict('r')

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
    hit_stats = soup.findAll('div', attrs={"class":"BoxscoreInfostyle__ContentWrapper-sc-1g9pw6v-4 jUDBeA"})
    
    if table_score == None:
        continue
    scores = table_score.find('tbody').find_all('tr')
    score1 = scores[0].find('td', attrs = {'data-col':'0'}).find('div').text
    score2 = scores[1].find('td', attrs = {'data-col':'0'}).find('div').text
    wins = '0'
    if int(score1) > int(score2):
        wins = '1'

    db.execute(f"UPDATE game_table SET away_score='{score1}', home_score = '{score2}', winner = '{wins}' WHERE game_id='{el['game_id']}';")
    k=0

    for i in range(len(atbats_tables)):
        team_name = atbats_tables[i].find('thead').find('tr').find('th', attrs = {'data-col':'0'})
        tbody = atbats_tables[i].find('tbody').find_all('tr')

        while k < 7:
            if hit_stats[k].find('span').text == 'BATTING':
                break
            k += 1

        stats = hit_stats[k].find_all('div')
        for i in range(len(stats)):
            if stats[i].find('span').text == '2B':
                doubles = stats[i].text.split(';')
                for i in range(len(doubles)):
                    name = doubles[i].split(' ')
                    if name[1].find('`') != -1:
                        continue
                    if name[1].find('\'') != -1:
                        continue
                    playerid = pd.read_sql(f"SELECT * FROM player_table WHERE p_name LIKE '%%{name[1]}%%';", con = db).to_dict('records')

                    if playerid != []:
                        if(len(name[2]) == 1) and (name[2]).isnumeric():
                            double = int(name[2])
                        else:
                            double = '1'

                        db.execute(f"UPDATE batter_table SET doubles='{double}' WHERE game_id='{el['game_id']}' AND playerid='{playerid[0]['p_id']}';")

            if stats[i].find('span').text == '3B':
                triples = stats[i].text.split(';')
                for i in range(len(doubles)):
                    name = doubles[i].split(' ')
                    if name[1].find('`') != -1:
                        continue
                    if name[1].find('\'') != -1:
                        continue
                    playerid = pd.read_sql(f"SELECT * FROM player_table WHERE p_name LIKE '%%{name[1]}%%';", con = db).to_dict('records')
                    if playerid != []:
                        if(len(name[2]) == 1) and (name[2]).isnumeric():
                            triple = int(name[2])
                        else:
                            triple = '1'

                        db.execute(f"UPDATE batter_table SET triples='{triple}' WHERE game_id='{el['game_id']}' AND playerid='{playerid[0]['p_id']}';")

            if stats[i].find('span').text == 'HR':
                homeruns = stats[i].text.split(';')
                for i in range(len(doubles)):
                    name = doubles[i].split(' ')
                    if name[1].find('`') != -1:
                        continue
                    if name[1].find('\'') != -1:
                        continue
                    playerid = pd.read_sql(f"SELECT * FROM player_table WHERE p_name LIKE '%%{name[1]}%%';", con = db).to_dict('records')
                    if playerid != []:
                        if(len(name[2]) == 1) and (name[2]).isnumeric():
                            homerun = int(name[2])
                        else:
                            homerun = '1'
                        db.execute(f"UPDATE batter_table SET homeruns='{homerun}' WHERE game_id='{el['game_id']}' AND playerid='{playerid[0]['p_id']}';")
        k += 1

        for i in range(9):
            url = tbody[i].find('td', attrs = {'data-col':'0'}).find('div').find('span').find('a').get('href')
            p_attabt = tbody[i].find('td', attrs = {'data-col':'1'}).find('span').text
            p_runs = tbody[i].find('td', attrs = {'data-col':'2'}).find('span').text
            p_hits = tbody[i].find('td', attrs = {'data-col':'3'}).find('span').text
            p_rbi = tbody[i].find('td', attrs = {'data-col':'4'}).find('span').text
            p_baseOnBall = tbody[i].find('td', attrs = {'data-col':'5'}).find('span').text
            p_strikeOut = tbody[i].find('td', attrs = {'data-col':'6'}).find('span').text
            p_id = url.split("/")[-1]

            hits = pd.read_sql(f"SELECT doubles, triples, homeruns FROM batter_table WHERE game_id='{el['game_id']}' AND playerid='{p_id}';", con = db).to_dict('records')

            if hits == []:
                break
            slg, obp, ops, avg = 0.0, 0.0, 0.0, 0.0
            if float(p_attabt) != 0.0:
                slg = (float(p_baseOnBall) + 2 * float(hits[0]['doubles']) + 3 * float(hits[0]['triples']) + 4 * float(hits[0]['homeruns'])) / float(p_attabt)
                obp = (float(p_hits) + float(p_baseOnBall)) / (float(p_attabt) + float(p_baseOnBall))
                ops = float(obp) + float(slg)
                avg = float(p_hits) / float(p_attabt)
            else:
                if float(p_baseOnBall) != 0.0:
                    avg = 0.0
                    slg = 0.0
                    obp = (float(p_hits) + float(p_baseOnBall)) / (float(p_attabt) + float(p_baseOnBall))
                    ops = float(obp) + float(slg)
                else:
                    slg = 0.0
                    obp = 0.0
                    ops = 0.0
                    avg = 0.0

            test = f"UPDATE batter_table SET atbats='{p_attabt}', avg = '{avg}', baseonballs = '{p_baseOnBall}', hits = '{p_hits}', obp = '{obp}', ops = '{ops}', rbi = '{p_rbi}', runs = '{p_runs}', slg = '{slg}', strikeouts = '{p_strikeOut}' WHERE game_id='{el['game_id']}' AND playerid='{p_id}';"

            db.execute(test)
            
driver.quit()

print("success!")