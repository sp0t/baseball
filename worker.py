from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy import text
from datetime import datetime, date

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
service = Service(executable_path='/usr/bin/chromedriver')
options = Options()
driver = webdriver.Chrome(service=service, options=options)
# driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()))


res = mlb.get('teams', params={'sportId':1})['teams']

team_dict = [{k:v for k,v in el.items() if k in ['name', 'abbreviation', 'clubName']} for el in res]

engine.execute(text("DROP TABLE IF EXISTS team_table;"))
engine.execute(text("DROP TABLE IF EXISTS player_table;"))

engine.execute(text("CREATE TABLE IF NOT EXISTS team_table(team_id TEXT, team_name TEXT, team_abbr TEXT, club_name TEXT);"))
engine.execute(text("CREATE TABLE IF NOT EXISTS player_table(p_id TEXT, p_name TEXT, t_id TEXT);"))

print(team_dict)