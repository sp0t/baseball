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
start_date = datetime.strptime("2024/02/20", "%Y/%m/%d")
end_date = datetime.strptime("2024/12/30", "%Y/%m/%d")

# Initialize the current date to the start date
current_date = start_date

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# driver = webdriver.Chrome('/home/.wdm/drivers/chromedriver',chrome_options=chrome_options)
driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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



url = f"https://www.mlb.com/schedule/2024-02-22"
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
    if empty_container == None:
        teams_container = game_container.find('div', attrs={"data-mlb-test": "scoreOrState"})
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


# atbats_tables = soup.findAll('table', attrs={"class":"tablestyle__StyledTable-sc-wsl6eq-0 kfhorh BoxscoreTeamTablestyle__TeamTable-sc-15fvlso-1 dgwGLd batters"})
# table_score = soup.find('table', attrs={"class":"tablestyle__StyledTable-sc-wsl6eq-0 bqIWWu"})
# hit_stats = soup.findAll('div', attrs={"class":"BoxscoreInfostyle__ContentWrapper-sc-1g9pw6v-4 jUDBeA"})

# if table_score == None:
#     continue
# scores = table_score.find('tbody').find_all('tr')
# score1 = scores[0].find('td', attrs = {'data-col':'0'}).find('div').text
# score2 = scores[1].find('td', attrs = {'data-col':'0'}).find('div').text
# wins = '1'
# if int(score1) > int(score2):
#     wins = '0'

# db.execute(f"UPDATE game_table SET away_score='{score1}', home_score = '{score2}', winner = '{wins}' WHERE game_id='{el['game_id']}';")
# k=0

# for i in range(len(atbats_tables)):
#     team_name = atbats_tables[i].find('thead').find('tr').find('th', attrs = {'data-col':'0'})
#     tbody = atbats_tables[i].find('tbody').find_all('tr')

#     name_id = {}

#     for i in range(len(tbody) - 1):
#         purl = tbody[i].find('td', attrs = {'data-col':'0'}).find('div').find('span').find('a').get('href')
#         if purl == None:
#             continue
#         p_id = purl.split("/")[-1]
#         text = tbody[i].find('td', attrs = {'data-col':'0'}).find('div').find('span').find('a').text
#         name_id[text] = p_id

#     while k < 7:
#         if hit_stats[k].find('span').text == 'BATTING':
#             break
#         k += 1

#     stats = hit_stats[k].find_all('div')
#     for i in range(len(stats)):
#         playerid = []

#         if stats[i].find('span').text == '2B':
#             doubles = stats[i].text.split(';')
#             for j in range(len(doubles)):
                
#                 for key in name_id:
#                     if doubles[j].find(key) != -1:
#                         playerid = name_id[key]
#                         num = '1'
#                         if doubles[j][doubles[j].find(key) + len(key) + 1].isnumeric():
#                             num = doubles[j][doubles[j].find(key) + len(key) + 1]
#                         db.execute(f"UPDATE batter_table SET doubles='{num}' WHERE game_id='{el['game_id']}' AND playerid='{playerid}';")
#                         break
#         if stats[i].find('span').text == '3B':
#             triples = stats[i].text.split(';')
#             for j in range(len(triples)):
#                 for key in name_id:
#                     if triples[j].find(key) != -1:
#                         playerid = name_id[key]
#                         num = '1'
#                         if triples[j][triples[j].find(key) + len(key) + 1].isnumeric():
#                             num = triples[j][triples[j].find(key) + len(key) + 1]
#                         db.execute(f"UPDATE batter_table SET triples='{num}' WHERE game_id='{el['game_id']}' AND playerid='{playerid}';")
#                         break


#         if stats[i].find('span').text == 'HR':
#             homeruns = stats[i].text.split(';')
#             for j in range(len(homeruns)):
#                 for key in name_id:
#                     if homeruns[j].find(key) != -1:
#                         playerid = name_id[key]
#                         num = '1'
#                         if homeruns[j][homeruns[j].find(key) + len(key) + 1].isnumeric():
#                             num = homeruns[j][homeruns[j].find(key) + len(key) + 1]
#                         db.execute(f"UPDATE batter_table SET homeruns='{num}' WHERE game_id='{el['game_id']}' AND playerid='{playerid}';")
#                         break

#     k += 1

#     for i in range(len(tbody) - 1):
#         print(i)
#         url = tbody[i].find('td', attrs = {'data-col':'0'}).find('div').find('span').find('a').get('href')
#         p_attabt = tbody[i].find('td', attrs = {'data-col':'1'}).find('span').text
#         p_runs = tbody[i].find('td', attrs = {'data-col':'2'}).find('span').text
#         p_hits = tbody[i].find('td', attrs = {'data-col':'3'}).find('span').text
#         p_rbi = tbody[i].find('td', attrs = {'data-col':'4'}).find('span').text
#         p_baseOnBall = tbody[i].find('td', attrs = {'data-col':'5'}).find('span').text
#         p_strikeOut = tbody[i].find('td', attrs = {'data-col':'6'}).find('span').text
#         p_id = url.split("/")[-1]
#         print(p_id)

#         hits = pd.read_sql(f"SELECT doubles, triples, homeruns FROM batter_table WHERE game_id='{el['game_id']}' AND playerid='{p_id}';", con = db).to_dict('records')
#         print(hits)

#         if hits == []:
#             continue
#         slg, obp, ops, avg = 0.0, 0.0, 0.0, 0.0
#         if float(p_attabt) != 0.0:
#             slg = ((float(p_hits) - float(hits[0]['doubles']) - float(hits[0]['triples']) - float(hits[0]['homeruns']))+ 4 * float(hits[0]['doubles']) + 5 * float(hits[0]['triples']) + 4 * float(hits[0]['homeruns'])) / float(p_attabt)
#             obp = (float(p_hits) + float(p_baseOnBall)) / (float(p_attabt) + float(p_baseOnBall))
#             ops = float(obp) + float(slg)
#             avg = float(p_hits) / float(p_attabt)
#         else:
#             if float(p_baseOnBall) != 0.0:
#                 avg = 0.0
#                 slg = 0.0
#                 obp = (float(p_hits) + float(p_baseOnBall)) / (float(p_attabt) + float(p_baseOnBall))
#                 ops = float(obp) + float(slg)
#             else:
#                 slg = 0.0
#                 obp = 0.0
#                 ops = 0.0
#                 avg = 0.0

#         test = f"UPDATE batter_table SET atbats='{p_attabt}', avg = '{avg}', baseonballs = '{p_baseOnBall}', hits = '{p_hits}', obp = '{obp}', ops = '{ops}', rbi = '{p_rbi}', runs = '{p_runs}', slg = '{slg}', strikeouts = '{p_strikeOut}' WHERE game_id='{el['game_id']}' AND playerid='{p_id}';"
#         db.execute(test)
#         print(test)
        
# db.execute(f"UPDATE game_table SET ck = '1' WHERE game_id='{el['game_id']}';")
# print(el['game_date'], el['game_id'], away_team, home_team, 'complete')

driver.quit()

print("success!")

