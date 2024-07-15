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
driver = webdriver.Chrome('/usr/bin/chromedriver',chrome_options=chrome_options)


def connect_to_db(): 
    
    try: 
        engine = create_engine('postgresql://postgres:lucamlb123@localhost:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        # engine = create_engine('postgresql://postgres:lucamlb123@ec2-3-115-115-146.ap-northeast-1.compute.amazonaws.com:5432/betmlb', connect_args = {'connect_timeout': 10}, echo=False, pool_size=20, max_overflow=0)
        # engine = create_engine('postgresql://postgres:postgres@localhost:5432/luca', 
        #                        connect_args = {'connect_timeout': 10}, 
        #                        echo=False, pool_size=20, max_overflow=0)
        print('Connection Initiated')
    except:
        raise ValueError("Can't connect to Heroku PostgreSQL! You must be so embarrassed")
    return engine

engine = connect_to_db()
engine.execute(text("CREATE TABLE IF NOT EXISTS win_probability(game_id TEXT, game_date TEXT, line TEXT, awaywp TEXT, hommewp TEXT);"))



res_game = pd.read_sql(text(f"SELECT * FROM game_table;"), con = engine).to_dict('records')
for game in res_game:
    date_object = datetime.strptime(game['game_date'], '%Y/%m/%d')
    date_string = date_object.strftime('%m/%d/%Y')
    url = f"https://baseballsavant.mlb.com/gamefeed?date={date_string}&gamePk={game['game_id']}&chartType=pitch&leg[…]Filter=&resultFilter=&hf=winProbability&sportId=1&liveAb="
    wait = WebDriverWait(driver, 10)
    get_url = driver.current_url
    wait.until(EC.url_to_be(url))

    page_source = driver.page_source
    soup = BeautifulSoup(page_source)
    print(soup)